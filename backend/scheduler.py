import time
import logging
import webbrowser
import urllib.parse
import pyperclip
import pyautogui
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')


# ─── WhatsApp Sender ─────────────────────────────────────────────────────────

def send_via_whatsapp_web(phone: str, message: str) -> bool:
    """
    Opens WhatsApp Web with the pre-filled message and auto-sends it.

    Strategy:
      1. Build the wa.me link (pre-fills the message in WhatsApp Web chat)
      2. Open it in the default browser
      3. Wait for WhatsApp Web to load
      4. Press Enter to send the message
      5. Wait briefly, then close the tab

    Returns True on success, False on failure.
    """
    try:
        # Sanitise phone number
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')

        # URL-encode the message for the wa.me link
        encoded_message = urllib.parse.quote(message)
        wa_link = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded_message}"

        logger.info(f"[WhatsApp] Opening: {wa_link}")
        webbrowser.open(wa_link)

        # Give WhatsApp Web time to open and load the chat
        logger.info("[WhatsApp] Waiting 20s for WhatsApp Web to load…")
        time.sleep(20)

        # Press Enter to send the pre-filled message
        pyautogui.press('enter')
        logger.info("[WhatsApp] Pressed Enter — message sent!")

        # Wait 3 seconds, then close the tab with Ctrl+W
        time.sleep(3)
        pyautogui.hotkey('ctrl', 'w')
        logger.info("[WhatsApp] Closed the tab.")

        return True

    except Exception as e:
        logger.error(f"[WhatsApp] Failed to send via WhatsApp Web: {e}")
        return False


def send_via_wa_link(phone: str, message: str) -> bool:
    """Fallback: just open the wa.me link without auto-sending."""
    try:
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
        encoded = urllib.parse.quote(message)
        link = f"https://wa.me/{phone_clean}?text={encoded}"
        webbrowser.open(link)
        logger.info(f"[WhatsApp Fallback] Opened wa.me link for {phone}")
        return True
    except Exception as e:
        logger.error(f"[WhatsApp Fallback] Error: {e}")
        return False


# ─── Scheduler Job ───────────────────────────────────────────────────────────

def check_and_send_wishes(app):
    """Background job that runs every minute to check for due schedules."""
    with app.app_context():
        from models import db, Schedule

        now = datetime.now()
        due = Schedule.query.filter(
            Schedule.sent == False,
            Schedule.scheduled_datetime <= now
        ).all()

        if not due:
            return

        logger.info(f"[Scheduler] Found {len(due)} due schedule(s) at {now.strftime('%H:%M:%S')}")

        for schedule in due:
            logger.info(f"[Scheduler] Processing: {schedule.name} → {schedule.phone}")

            success = send_via_whatsapp_web(schedule.phone, schedule.message)

            if not success:
                logger.warning(f"[Scheduler] Primary method failed, using fallback for {schedule.name}")
                send_via_wa_link(schedule.phone, schedule.message)

            schedule.sent = True
            db.session.commit()
            logger.info(f"[Scheduler] ✅ Marked schedule {schedule.id} ({schedule.name}) as sent.")


def start_scheduler(app):
    """Start the APScheduler background scheduler."""
    scheduler.add_job(
        func=check_and_send_wishes,
        args=[app],
        trigger='interval',
        seconds=30,   # Check every 30 seconds for faster response
        id='wish_checker',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started — checking every 30 seconds.")
