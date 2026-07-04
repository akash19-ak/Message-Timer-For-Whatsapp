from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from models import db, Schedule


def parse_and_localize(dt_str):
    """Parse ISO datetime string and return a naive local datetime.

    JS sends UTC ISO strings with Z suffix (e.g. '2026-07-04T07:50:00.000Z').
    Python's datetime.now() returns naive local time.
    We convert the incoming UTC time to local naive so comparisons work.
    """
    # Normalize: replace Z with +00:00 so Python can parse it
    dt_str_norm = dt_str.replace('Z', '+00:00')
    dt = datetime.fromisoformat(dt_str_norm)

    if dt.tzinfo is not None:
        # It's tz-aware (UTC from JS). Convert to local naive.
        dt = dt.astimezone().replace(tzinfo=None)
    # else: already naive (no timezone info) — use as-is
    return dt

api = Blueprint('api', __name__)


@api.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Return all scheduled birthday wishes."""
    schedules = Schedule.query.order_by(Schedule.scheduled_datetime.asc()).all()
    return jsonify([s.to_dict() for s in schedules]), 200


@api.route('/api/schedule', methods=['POST'])
def create_schedule():
    """Create a new scheduled birthday wish."""
    data = request.get_json()

    required = ['name', 'phone', 'message', 'scheduled_datetime']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        scheduled_dt = parse_and_localize(data['scheduled_datetime'])
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid datetime format. Use ISO 8601. ({e})'}), 400

    if scheduled_dt <= datetime.now():
        return jsonify({'error': 'Scheduled time must be in the future.'}), 400

    schedule = Schedule(
        name=data['name'],
        phone=data['phone'],
        message=data['message'],
        scheduled_datetime=scheduled_dt
    )
    db.session.add(schedule)
    db.session.commit()

    return jsonify(schedule.to_dict()), 201


@api.route('/api/schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a scheduled birthday wish by ID."""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found.'}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': f'Schedule {schedule_id} deleted successfully.'}), 200


@api.route('/api/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing scheduled birthday wish."""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found.'}), 404

    data = request.get_json()

    if data.get('name'):
        schedule.name = data['name']
    if data.get('phone'):
        schedule.phone = data['phone']
    if data.get('message'):
        schedule.message = data['message']
    if data.get('scheduled_datetime'):
        try:
            scheduled_dt = parse_and_localize(data['scheduled_datetime'])
            if scheduled_dt <= datetime.now():
                return jsonify({'error': 'Scheduled time must be in the future.'}), 400
            schedule.scheduled_datetime = scheduled_dt
            schedule.sent = False  # Reset sent status on reschedule
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid datetime format. ({e})'}), 400

    db.session.commit()
    return jsonify(schedule.to_dict()), 200


@api.route('/api/schedule/<int:schedule_id>/send', methods=['POST'])
def send_now(schedule_id):
    """Manually trigger sending a WhatsApp message for a schedule."""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found.'}), 404

    from scheduler import send_via_whatsapp_web, send_via_wa_link
    import threading

    def do_send():
        success = send_via_whatsapp_web(schedule.phone, schedule.message)
        if not success:
            send_via_wa_link(schedule.phone, schedule.message)
        schedule.sent = True
        db.session.commit()

    # Run in a background thread so we don't block the HTTP response
    t = threading.Thread(target=do_send, daemon=True)
    t.start()

    return jsonify({'message': f'WhatsApp message triggered for {schedule.name}. Check your browser!'}), 200
