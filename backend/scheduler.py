import time
import logging
import webbrowser
import urllib.parse
import pyautogui
import pyperclip
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')


# ─── WhatsApp Sender ─────────────────────────────────────────────────────────

def sanitize_phone(phone: str) -> str:
    """
    Return a clean phone number string with leading +.
    pywhatkit requires the number to start with + and country code.
    e.g.  '919876543210'  →  '+919876543210'
          '+919876543210' →  '+919876543210'
    """
    cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned


def send_via_pywhatkit(phone: str, message: str, wait_time: int = 25) -> bool:
    """
    Send a WhatsApp message using pywhatkit (WhatsApp Web automation).

    Steps pywhatkit takes internally:
      1. Opens https://web.whatsapp.com/send?phone=<phone>&text=<message>
      2. Clicks the center of screen to focus the chat window
      3. Waits `wait_time` seconds for WhatsApp Web to load the chat
      4. Presses Enter to send the message

    Requirements:
      - User must be logged in to WhatsApp Web (wa.me QR already scanned)
      - A browser must be set as default (Chrome / Edge)
    """
    import pywhatkit as kit

    phone_clean = sanitize_phone(phone)
    logger.info(f"[WhatsApp] Sending to {phone_clean} via pywhatkit (wait={wait_time}s)…")

    try:
        kit.sendwhatmsg_instantly(
            phone_no=phone_clean,
            message=message,
            wait_time=wait_time,   # seconds to wait for WhatsApp Web to load
            tab_close=True,        # close tab after sending
            close_time=3,          # seconds before closing
        )
        logger.info(f"[WhatsApp] ✅ Message sent to {phone_clean}")
        return True

    except Exception as e:
        logger.error(f"[WhatsApp] pywhatkit error for {phone_clean}: {e}")
        return False


def send_via_wa_link(phone: str, message: str) -> bool:
    """
    Fallback: open the wa.me link so user can send manually.
    Also uses pyautogui to press Enter after waiting.
    """
    try:
        phone_clean = phone.replace('+', '').replace(' ', '').replace('-', '')
        encoded = urllib.parse.quote(message)
        link = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded}"

        logger.info(f"[WhatsApp Fallback] Opening: {link}")
        webbrowser.open(link)

        # Wait for page to load then try pressing Enter
        time.sleep(25)
        # Click middle of screen to ensure WhatsApp chat has focus
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(2)
        pyautogui.press('enter')
        logger.info(f"[WhatsApp Fallback] Pressed Enter for {phone_clean}")

        time.sleep(3)
        pyautogui.hotkey('ctrl', 'w')
        return True

    except Exception as e:
        logger.error(f"[WhatsApp Fallback] Error: {e}")
        return False


# ─── Scheduler Job ───────────────────────────────────────────────────────────

def check_and_send_wishes(app):
    """Background job that runs every 30 seconds to check for due schedules."""
    with app.app_context():
        from models import db, Schedule

        now = datetime.now()
        due = Schedule.query.filter(
            Schedule.sent == False,
            Schedule.scheduled_datetime <= now
        ).all()

        if not due:
            return

        logger.info(f"[Scheduler] {len(due)} due schedule(s) found at {now.strftime('%H:%M:%S')}")

        for schedule in due:
            logger.info(f"[Scheduler] Processing: {schedule.name} → {schedule.phone}")

            success = send_via_pywhatkit(schedule.phone, schedule.message, wait_time=25)

            if not success:
                logger.warning(f"[Scheduler] pywhatkit failed, trying fallback for {schedule.name}")
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
        seconds=30,
        id='wish_checker',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started — checking every 30 seconds.")
