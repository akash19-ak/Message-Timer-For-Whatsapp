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
        
        # Invoke powershell Set-Clipboard command
        cmd = ["powershell", "-Command", f"Set-Clipboard -Path '{abs_path}'"]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        logger.error(f"[Clipboard] Failed to copy image to clipboard: {e}")
        return False


# ─── Method 1: WhatsApp Desktop App ─────────────────────────────────────────

def send_via_whatsapp_app(phone: str, message: str, wait_time: int = 12, image_filename: str = None) -> bool:
    """
    Send via the WhatsApp Desktop app (Windows).
    """
    try:
        import pygetwindow as gw
        
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

        # Wait for WhatsApp app to open and load the chat
        logger.info(f"[WA App] Waiting {wait_time}s for WhatsApp app to load…")
        time.sleep(wait_time)

        # Bring WhatsApp to the front and ensure it is maximized
        try:
            wins = gw.getWindowsWithTitle('WhatsApp')
            if wins:
                win = wins[0]
                win.maximize()
                win.activate()
                time.sleep(1)
        except Exception as e:
            logger.warning(f"[WA App] Could not activate window: {e}")

        # Send
        if has_image:
            logger.info("[WA App] Pasting image and writing caption...")
            keyboard.send('ctrl+v')
            time.sleep(1.5)  # Wait for attachment modal to display
            
            # Type message into the caption box
            keyboard.write(message)
            time.sleep(0.5)
            
            # Press enter to send image with caption
            keyboard.send('enter')
            time.sleep(1)
            logger.info(f"[WA App] ✅ Image sent via WhatsApp Desktop to {phone_clean}")
        else:
            logger.info("[WA App] Pressing Enter to send...")
            keyboard.send('enter')
            time.sleep(1)
            keyboard.send('enter')
            logger.info(f"[WA App] ✅ Enter pressed — message sent via WhatsApp Desktop to {phone_clean}")

        time.sleep(1)
        return True

    except Exception as e:
        logger.error(f"[WA App] Failed: {e}")
        return False


# ─── Method 2: WhatsApp Web (Browser) ────────────────────────────────────────

def send_via_whatsapp_web(phone: str, message: str, wait_time: int = 30, image_filename: str = None) -> bool:
    """
    Send via WhatsApp Web in the default browser.
    """
    try:
        import pygetwindow as gw
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

            logger.info(f"[WA Web] Waiting {wait_time}s for WhatsApp Web to load…")
            time.sleep(wait_time)

            # Focus browser window
            try:
                titles = gw.getAllTitles()
                wa_titles = [t for t in titles if 'WhatsApp' in t]
                if wa_titles:
                    win = gw.getWindowsWithTitle(wa_titles[0])[0]
                    win.maximize()
                    win.activate()
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"[WA Web] Could not activate window: {e}")

            logger.info("[WA Web] Pasting image and writing caption...")
            keyboard.send('ctrl+v')
            time.sleep(2.0)  # Web might need a tiny bit longer to process clipboard
            
            # Type message
            keyboard.write(message)
            time.sleep(0.5)
            
            # Press enter to send image
            keyboard.send('enter')
            time.sleep(1)
            logger.info(f"[WA Web] ✅ Image with caption sent to {phone_clean}")
            return True
        else:
            import pywhatkit as kit
            logger.info(f"[WA Web] Sending via pywhatkit (wait={wait_time}s)…")
            kit.sendwhatmsg_instantly(
                phone_no=phone_clean,
                message=message,
                wait_time=wait_time,
                tab_close=False  # Do not close the tab so we don't interrupt the send process
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
        seconds=30,
        id='wish_checker',
        replace_existing=True
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler started — checking every 30 seconds.")
