import os
import time
import logging
import subprocess
import webbrowser
import urllib.parse
import pyautogui
import pyperclip
import keyboard
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

# Disable pyautogui fail-safe (moving mouse to corner won't abort)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.02  # Reduced from 0.05 — faster pyautogui ops


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


# ─── Clipboard Helper ────────────────────────────────────────────────────────

def copy_image_to_clipboard(image_filename: str) -> bool:
    """Copy the image file to Windows clipboard using PowerShell."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'uploads', image_filename)

        if not os.path.exists(file_path):
            logger.error(f"[Clipboard] File not found: {file_path}")
            return False

        abs_path = os.path.normpath(file_path)
        logger.info(f"[Clipboard] Copying image to clipboard: {abs_path}")

        # -NoProfile / -NonInteractive speeds up PowerShell startup
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive",
            "-Command", f"Set-Clipboard -Path '{abs_path}'"
        ]
        subprocess.run(cmd, check=True, timeout=5)
        return True
    except Exception as e:
        logger.error(f"[Clipboard] Failed to copy image to clipboard: {e}")
        return False


# ─── Window Activator (shared) ───────────────────────────────────────────────

def _activate_window(title_keyword: str, timeout: float = 4.0) -> bool:
    """
    Poll for a window containing title_keyword and activate it.
    Returns True if found within timeout seconds.
    Much faster than a single fixed sleep — exits as soon as window appears.
    """
    try:
        import pygetwindow as gw
        deadline = time.time() + timeout
        while time.time() < deadline:
            wins = [w for w in gw.getAllWindows() if title_keyword.lower() in w.title.lower()]
            if wins:
                win = wins[0]
                try:
                    win.maximize()
                    win.activate()
                except Exception:
                    pass
                time.sleep(0.2)
                return True
            time.sleep(0.25)
    except Exception as e:
        logger.warning(f"[Window] Could not activate '{title_keyword}': {e}")
    return False


# ─── Method 1: WhatsApp Desktop App ─────────────────────────────────────────

def send_via_whatsapp_app(phone: str, message: str, wait_time: int = 6, image_filename: str = None) -> bool:
    """
    Send via the WhatsApp Desktop app (Windows).
    wait_time: seconds to wait for WhatsApp to open the chat (default: 6s)
    """
    try:
        phone_clean = phone_digits_only(phone)

        has_image = False
        if image_filename:
            if copy_image_to_clipboard(image_filename):
                has_image = True
            else:
                logger.warning("[WA App] Could not copy image to clipboard, falling back to text-only.")

        if has_image:
            uri = f"whatsapp://send?phone={phone_clean}"
        else:
            encoded_msg = urllib.parse.quote(message)
            uri = f"whatsapp://send?phone={phone_clean}&text={encoded_msg}"

        logger.info(f"[WA App] Opening WhatsApp Desktop for {phone_clean}…")
        os.startfile(uri)

        # Poll for WhatsApp window instead of sleeping a fixed amount
        logger.info(f"[WA App] Waiting up to {wait_time}s for WhatsApp to load…")
        found = _activate_window('WhatsApp', timeout=wait_time)
        if not found:
            logger.warning("[WA App] WhatsApp window not found in time — attempting keyboard anyway.")
        else:
            time.sleep(0.4)  # tiny settle after activation

        # Send
        if has_image:
            logger.info("[WA App] Pasting image and writing caption...")
            keyboard.send('ctrl+v')
            time.sleep(1.0)  # Wait for attachment modal (reduced from 1.5s)

            keyboard.write(message)
            time.sleep(0.3)

            keyboard.send('enter')
            time.sleep(0.5)
            logger.info(f"[WA App] ✅ Image sent via WhatsApp Desktop to {phone_clean}")
        else:
            logger.info("[WA App] Pressing Enter to send...")
            keyboard.send('enter')
            time.sleep(0.4)
            keyboard.send('enter')
            logger.info(f"[WA App] ✅ Message sent via WhatsApp Desktop to {phone_clean}")

        return True

    except Exception as e:
        logger.error(f"[WA App] Failed: {e}")
        return False


# ─── Method 2: WhatsApp Web (Browser) ────────────────────────────────────────

def send_via_whatsapp_web(phone: str, message: str, wait_time: int = 8, image_filename: str = None) -> bool:
    """
    Send via WhatsApp Web in the default browser.
    wait_time: seconds to wait for WhatsApp Web to load (default: 8s)
    """
    try:
        phone_clean = phone_digits_only(phone)

        has_image = False
        if image_filename:
            if copy_image_to_clipboard(image_filename):
                has_image = True
            else:
                logger.warning("[WA Web] Could not copy image to clipboard, falling back to text-only.")

        if has_image:
            url = f"https://web.whatsapp.com/send?phone={phone_clean}"
            logger.info(f"[WA Web] Opening: {url} (with image attachment)")
            webbrowser.open(url)

            logger.info(f"[WA Web] Waiting up to {wait_time}s for WhatsApp Web to load…")
            found = _activate_window('WhatsApp', timeout=wait_time)
            if found:
                time.sleep(0.4)

            logger.info("[WA Web] Pasting image and writing caption...")
            keyboard.send('ctrl+v')
            time.sleep(1.2)  # Web image processing (reduced from 2.0s)

            keyboard.write(message)
            time.sleep(0.3)

            keyboard.send('enter')
            time.sleep(0.5)
            logger.info(f"[WA Web] ✅ Image with caption sent to {phone_clean}")
            return True
        else:
            # Text-only path: use pywhatkit with minimal wait
            import pywhatkit as kit
            logger.info(f"[WA Web] Sending via pywhatkit (wait={wait_time}s)…")
            kit.sendwhatmsg_instantly(
                phone_no=phone_clean,
                message=message,
                wait_time=wait_time,
                tab_close=False
            )
            logger.info(f"[WA Web] ✅ Message sent to {phone_clean}")
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

def send_message(phone: str, message: str, method: str = 'app', image_filename: str = None) -> bool:
    """
    Send a WhatsApp message using the specified method.
    method: 'app' | 'web' | 'link'
    Falls back to the next method on failure.
    """
    if method == 'app':
        success = send_via_whatsapp_app(phone, message, image_filename=image_filename)
        if not success:
            logger.warning("[Sender] App method failed, falling back to web…")
            success = send_via_whatsapp_web(phone, message, image_filename=image_filename)
        if not success:
            send_via_wa_link(phone, message)
        return success

    elif method == 'web':
        success = send_via_whatsapp_web(phone, message, image_filename=image_filename)
        if not success:
            logger.warning("[Sender] Web method failed, falling back to link…")
            send_via_wa_link(phone, message)
        return success

    else:  # 'link'
        return send_via_wa_link(phone, message)


# ─── Scheduler Job ────────────────────────────────────────────────────────────

def check_and_send_wishes(app):
    """Background job — runs every 5 seconds, sends due scheduled wishes."""
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
            method         = getattr(schedule, 'send_method', None) or 'app'
            image_filename = getattr(schedule, 'image_filename', None)
            send_message(schedule.phone, schedule.message, method=method, image_filename=image_filename)
            schedule.sent = True
            db.session.commit()
            logger.info(f"[Scheduler] ✅ Done — schedule {schedule.id} marked sent.")


def start_scheduler(app):
    scheduler.add_job(
        func=check_and_send_wishes,
        args=[app],
        trigger='interval',
        seconds=5,          # ⚡ was 30s — now checks every 5 seconds for near-instant delivery
        id='wish_checker',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started — checking every 5 seconds.")
