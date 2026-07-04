import webbrowser
import urllib.parse
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

def check_and_send_wishes(app):
    """Background job that runs every minute to check for due schedules."""
    with app.app_context():
        from models import db, Schedule

        now = datetime.now()
        # Find unsent schedules whose time has arrived (within the current minute)
        due = Schedule.query.filter(
            Schedule.sent == False,
            Schedule.scheduled_datetime <= now
        ).all()

        for schedule in due:
            try:
                phone = schedule.phone.replace('+', '').replace(' ', '').replace('-', '')
                encoded_message = urllib.parse.quote(schedule.message)
                wa_link = f"https://wa.me/{phone}?text={encoded_message}"

                logger.info(f"[Scheduler] Opening WhatsApp for {schedule.name} → {wa_link}")
                webbrowser.open(wa_link)

                schedule.sent = True
                db.session.commit()
                logger.info(f"[Scheduler] Marked schedule {schedule.id} as sent.")
            except Exception as e:
                logger.error(f"[Scheduler] Error processing schedule {schedule.id}: {e}")


def start_scheduler(app):
    """Start the APScheduler background scheduler."""
    scheduler.add_job(
        func=check_and_send_wishes,
        args=[app],
        trigger='interval',
        minutes=1,
        id='wish_checker',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started — checking every minute.")
