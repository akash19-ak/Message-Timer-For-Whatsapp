from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Schedule

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
        scheduled_dt = datetime.fromisoformat(data['scheduled_datetime'])
    except ValueError:
        return jsonify({'error': 'Invalid datetime format. Use ISO 8601.'}), 400

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
            scheduled_dt = datetime.fromisoformat(data['scheduled_datetime'])
            if scheduled_dt <= datetime.now():
                return jsonify({'error': 'Scheduled time must be in the future.'}), 400
            schedule.scheduled_datetime = scheduled_dt
            schedule.sent = False  # Reset sent status on reschedule
        except ValueError:
            return jsonify({'error': 'Invalid datetime format.'}), 400

    db.session.commit()
    return jsonify(schedule.to_dict()), 200
