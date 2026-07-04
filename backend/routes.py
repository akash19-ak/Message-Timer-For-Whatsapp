from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from models import db, Schedule

api = Blueprint('api', __name__)


# ─── Datetime helper ─────────────────────────────────────────────────────────

def parse_and_localize(dt_str: str) -> datetime:
    """
    Parse any ISO datetime string (with or without Z/offset) and return
    a naive datetime in the machine's local timezone for DB storage.

    JS sends UTC with Z suffix: '2026-07-04T07:50:00.000Z'
    Python datetime.now() is naive local time.
    We normalize to naive local so comparisons work correctly.
    """
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    if dt.tzinfo is not None:
        # tz-aware → convert to local timezone → strip tzinfo
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


VALID_METHODS = {'app', 'web', 'link'}


# ─── Routes ──────────────────────────────────────────────────────────────────

@api.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Return all scheduled birthday wishes."""
    schedules = Schedule.query.order_by(Schedule.scheduled_datetime.asc()).all()
    return jsonify([s.to_dict() for s in schedules]), 200


@api.route('/api/schedule', methods=['POST'])
def create_schedule():
    """Create a new scheduled birthday wish."""
    data = request.get_json()

    for field in ['name', 'phone', 'message', 'scheduled_datetime']:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    try:
        scheduled_dt = parse_and_localize(data['scheduled_datetime'])
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid datetime format. Use ISO 8601. ({e})'}), 400

    if scheduled_dt <= datetime.now():
        return jsonify({'error': 'Scheduled time must be in the future.'}), 400

    method = data.get('send_method', 'app')
    if method not in VALID_METHODS:
        method = 'app'

    schedule = Schedule(
        name=data['name'],
        phone=data['phone'],
        message=data['message'],
        scheduled_datetime=scheduled_dt,
        send_method=method,
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
    return jsonify({'message': f'Schedule {schedule_id} deleted.'}), 200


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
    if data.get('send_method') in VALID_METHODS:
        schedule.send_method = data['send_method']
    if data.get('scheduled_datetime'):
        try:
            scheduled_dt = parse_and_localize(data['scheduled_datetime'])
            if scheduled_dt <= datetime.now():
                return jsonify({'error': 'Scheduled time must be in the future.'}), 400
            schedule.scheduled_datetime = scheduled_dt
            schedule.sent = False
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid datetime format. ({e})'}), 400

    db.session.commit()
    return jsonify(schedule.to_dict()), 200


@api.route('/api/schedule/<int:schedule_id>/send', methods=['POST'])
def send_now(schedule_id):
    """
    Manually trigger sending a WhatsApp message for a schedule entry.
    Accepts optional JSON body: { "method": "app" | "web" | "link" }
    Defaults to the schedule's stored send_method.
    """
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found.'}), 404

    data = request.get_json(silent=True) or {}
    method = data.get('method', schedule.send_method or 'app')
    if method not in VALID_METHODS:
        method = 'app'

    from scheduler import send_message
    import threading
    from flask import current_app

    # Capture before threading (avoid SQLAlchemy detached session issues)
    phone   = schedule.phone
    message = schedule.message
    name    = schedule.name
    sid     = schedule.id
    app     = current_app._get_current_object()

    def do_send(app_obj):
        with app_obj.app_context():
            send_message(phone, message, method=method)
            # Update sent flag via raw SQL to avoid session issues in thread
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text(f"UPDATE schedules SET sent=1 WHERE id={sid}"))
                conn.commit()

    threading.Thread(target=do_send, args=(app,), daemon=True).start()

    method_labels = {
        'app':  'WhatsApp Desktop App',
        'web':  'WhatsApp Web (browser)',
        'link': 'wa.me link',
    }
    return jsonify({
        'message': f'Sending to {name} via {method_labels[method]}. Check your screen!'
    }), 200
