import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
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
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

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

    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            return jsonify({'error': 'Invalid image format. Only JPG, JPEG, PNG, GIF are allowed.'}), 400
        
        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        image_filename = unique_filename

    schedule = Schedule(
        name=data['name'],
        phone=data['phone'],
        message=data['message'],
        scheduled_datetime=scheduled_dt,
        send_method=method,
        image_filename=image_filename,
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
    
    # Delete file from disk
    if schedule.image_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], schedule.image_filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"Failed to remove file {file_path} on delete: {e}")

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': f'Schedule {schedule_id} deleted.'}), 200


@api.route('/api/schedule/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update an existing scheduled birthday wish."""
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({'error': 'Schedule not found.'}), 404

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

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

    image_file = request.files.get('image')
    if image_file and image_file.filename != '':
        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            return jsonify({'error': 'Invalid image format. Only JPG, JPEG, PNG, GIF are allowed.'}), 400
        
        # Delete old file
        if schedule.image_filename:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], schedule.image_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    current_app.logger.warning(f"Failed to remove old file {old_path}: {e}")

        filename = secure_filename(image_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        image_file.save(upload_path)
        schedule.image_filename = unique_filename
        schedule.sent = False
    elif data.get('remove_image') == 'true' or data.get('remove_image') is True:
        # Delete old file
        if schedule.image_filename:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], schedule.image_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    current_app.logger.warning(f"Failed to remove old file {old_path}: {e}")
        schedule.image_filename = None
        schedule.sent = False

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
    phone          = schedule.phone
    message        = schedule.message
    name           = schedule.name
    image_filename = schedule.image_filename
    sid            = schedule.id
    app            = current_app._get_current_object()

    def do_send(app_obj):
        with app_obj.app_context():
            send_message(phone, message, method=method, image_filename=image_filename)
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
