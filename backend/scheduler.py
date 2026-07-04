import os
import time
import logging
import subprocess
import webbrowser
import urllib.parse
import pyautogui
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

# Disable pyautogui fail-safe (moving mouse to corner won't abort)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


# ─── Phone Sanitization ───────────────────────────────────────────────────────

def sanitize_phone(phone: str) -> str:
    """Return a clean E.164 phone number with leading +."""
    cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned


def phone_digits_only(phone: str) -> str:
    """Return only the digits (no +)."""
    return phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')


# ─── Method 1: WhatsApp Desktop App ─────────────────────────────────────────

def send_via_whatsapp_app(phone: str, message: str, wait_time: int = 6) -> bool:
    """
    Send via the WhatsApp Desktop app (Windows).
    Uses the whatsapp:// URI scheme to open the installed WhatsApp app.
    
    Steps:
      1. Build whatsapp://send?phone=<phone>&text=<message>
      2. Open it with os.startfile() — launches WhatsApp Desktop
      3. Wait for app to open and load the chat (wait_time seconds)
      4. Click center of screen to focus the message input
      5. Press Enter to send
    """
    try:
        phone_clean = phone_digits_only(phone)
        encoded_msg = urllib.parse.quote(message)
        uri = f"whatsapp://send?phone={phone_clean}&text={encoded_msg}"

        logger.info(f"[WA App] Opening WhatsApp Desktop for {phone_clean}…")

        # Open the whatsapp:// URI — this launches the desktop app
        os.startfile(uri)

        # Wait for WhatsApp app to open and load the chat
        logger.info(f"[WA App] Waiting {wait_time}s for WhatsApp app to load…")
        time.sleep(wait_time)

        # Click the center-bottom of screen where the send button / input is
        screen_w, screen_h = pyautogui.size()
        # Click in the lower-center area (chat input box area)
        pyautogui.click(screen_w // 2, int(screen_h * 0.9))
        time.sleep(0.5)

        # Press Enter to send
        pyautogui.press('enter')
        logger.info(f"[WA App] ✅ Enter pressed — message sent via WhatsApp Desktop to {phone_clean}")

        time.sleep(1)
        return True

    except Exception as e:
        logger.error(f"[WA App] Failed: {e}")
        return False


# ─── Method 2: WhatsApp Web (Browser) ────────────────────────────────────────

def send_via_whatsapp_web(phone: str, message: str, wait_time: int = 30) -> bool:
    """
    Send via WhatsApp Web in the default browser.
    Opens web.whatsapp.com with phone + text pre-filled, waits for page load,
    then presses Enter. Does NOT close the tab automatically.

    Requirements: Must be logged in to WhatsApp Web in the default browser.
    """
    try:
        phone_clean = phone_digits_only(phone)
        encoded_msg = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={encoded_msg}"

        logger.info(f"[WA Web] Opening: {url}")
        webbrowser.open(url)

        # Give WhatsApp Web enough time to fully load the chat
        logger.info(f"[WA Web] Waiting {wait_time}s for WhatsApp Web to load…")
        time.sleep(wait_time)

        # Click the center of screen to ensure the chat window has focus
        screen_w, screen_h = pyautogui.size()
        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(1)

        # Press Enter to send
        pyautogui.press('enter')
        logger.info(f"[WA Web] ✅ Enter pressed — message sent via WhatsApp Web to {phone_clean}")

        time.sleep(2)
        return True

    except Exception as e:
        logger.error(f"[WA Web] Failed: {e}")
        return False


# ─── Method 3: wa.me Fallback (Manual) ───────────────────────────────────────

def send_via_wa_link(phone: str, message: str) -> bool:
    """Last resort: open the wa.me link so user can send manually."""
    try:
        phone_clean = phone_digits_only(phone)
        encoded = urllib.parse.quote(message)
        link = f"https://wa.me/{phone_clean}?text={encoded}"
        webbrowser.open(link)
        logger.info(f"[WA Link] Opened wa.me link for {phone_clean} (manual send required)")
        return True
    except Exception as e:
        logger.error(f"[WA Link] Error: {e}")
        return False


# ─── Unified Sender ───────────────────────────────────────────────────────────

def send_message(phone: str, message: str, method: str = 'app') -> bool:
    """
    Send a WhatsApp message using the specified method.
    method: 'app' | 'web' | 'link'
    Falls back to the next method on failure.
    """
    if method == 'app':
        success = send_via_whatsapp_app(phone, message)
        if not success:
            logger.warning("[Sender] App method failed, falling back to web…")
            success = send_via_whatsapp_web(phone, message)
        if not success:
            send_via_wa_link(phone, message)
        return success

    elif method == 'web':
        success = send_via_whatsapp_web(phone, message)
        if not success:
            logger.warning("[Sender] Web method failed, falling back to link…")
            send_via_wa_link(phone, message)
        return success

    else:  # 'link'
        return send_via_wa_link(phone, message)


# ─── Scheduler Job ────────────────────────────────────────────────────────────

def check_and_send_wishes(app):
    """Background job — runs every 30 seconds, sends due scheduled wishes."""
    with app.app_context():
        from models import db, Schedule

        now = datetime.now()
        due = Schedule.query.filter(
            Schedule.sent == False,
            Schedule.scheduled_datetime <= now
        ).all()

        if not due:
            return

        logger.info(f"[Scheduler] {len(due)} due wish(es) at {now.strftime('%H:%M:%S')}")

        for schedule in due:
            logger.info(f"[Scheduler] Sending to {schedule.name} ({schedule.phone})")
            method = getattr(schedule, 'send_method', None) or 'app'
            send_message(schedule.phone, schedule.message, method=method)
            schedule.sent = True
            db.session.commit()
            logger.info(f"[Scheduler] ✅ Done — schedule {schedule.id} marked sent.")


def start_scheduler(app):
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
