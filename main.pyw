"""
CopyCat - A simple clipboard typing utility

This program runs in the system tray and allows you to type the contents of your 
clipboard automatically using a hotkey (Ctrl+Alt+T by default).

Usage:
    1. Copy text to clipboard
    2. Press Ctrl+Alt+T to paste by typing (useful for applications that don't accept paste)
"""
# Standard library imports
import atexit
import os
import sys
import tempfile
import threading
import time

# Third-party imports
try:
    import pyperclip
    import pyautogui
    from pynput import keyboard
    from PIL import Image, ImageDraw
    from pystray import Icon, Menu, MenuItem
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please install required packages with: pip install pyperclip pyautogui pynput pillow pystray")
    sys.exit(1)


# Configuration
HOTKEY = '<ctrl>+<alt>+t'
TYPING_DELAY = 0.5  # seconds
TYPING_INTERVAL = 0  # seconds between keystrokes (0 = fastest)
LOCK_FILE = os.path.join(tempfile.gettempdir(), "copycat.lock")


# Global variables
ICON_INSTANCE = None
LOCK_FILE_HANDLE = None


# -------- Single Instance Check --------
def ensure_single_instance():
    """
    Ensures only one instance of CopyCat runs at a time.
    Uses a file lock mechanism which is more reliable than sockets.
    
    Returns:
        bool: True if this is the only instance, False if another instance is running
    """
    global LOCK_FILE_HANDLE
    
    if sys.platform == 'win32':
        try:
            import msvcrt
            try:
                with open(LOCK_FILE, 'w', encoding='utf-8') as lock_file:
                    LOCK_FILE_HANDLE = lock_file
                    try:
                        msvcrt.locking(LOCK_FILE_HANDLE.fileno(), msvcrt.LK_NBLCK, 1)
                        atexit.register(release_lock)
                        return True
                    except IOError:
                        return False
            except (IOError, OSError):
                return False
        except ImportError:
            return False
    else:
        try:
            import fcntl
            try:
                with open(LOCK_FILE, 'w', encoding='utf-8') as lock_file:
                    LOCK_FILE_HANDLE = lock_file
                    try:
                        fcntl.flock(LOCK_FILE_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        atexit.register(release_lock)
                        return True
                    except IOError:
                        return False
            except (IOError, OSError):
                return False
        except ImportError:
            return False
    
    return False


def release_lock():
    if LOCK_FILE_HANDLE:
        try:
            if sys.platform == 'win32':
                try:
                    import msvcrt
                    try:
                        msvcrt.locking(LOCK_FILE_HANDLE.fileno(), msvcrt.LK_UNLCK, 1)
                    except (IOError, OSError):
                        pass
                except ImportError:
                    pass
            else:
                try:
                    import fcntl
                    try:
                        fcntl.flock(LOCK_FILE_HANDLE, fcntl.LOCK_UN)
                    except (IOError, OSError):
                        pass
                except ImportError:
                    pass
            
            LOCK_FILE_HANDLE.close()
            try:
                os.remove(LOCK_FILE)
            except (IOError, OSError):
                pass
        except (IOError, OSError):
            pass


# -------- Typing Clipboard Text --------
def type_clipboard_text():
    try:
        time.sleep(TYPING_DELAY)
        text = pyperclip.paste()
        if not text:
            print("Clipboard is empty")
            return
        
        print("🐱 CopyCat typing clipboard...")
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            pyautogui.write(line, interval=TYPING_INTERVAL)
            
            if i < len(lines) - 1:
                pyautogui.hotkey('shift', 'enter')
        
        print("✓ Clipboard contents typed successfully")
    except (pyautogui.FailSafeException, KeyboardInterrupt) as e:
        error_msg = f"Typing interrupted: {e}"
        print(error_msg)
    except Exception as e:
        error_msg = f"Error typing clipboard: {e}"
        print(error_msg)


# -------- Hotkey Setup --------
def start_hotkey_listener():
    def on_activate():
        type_clipboard_text()

    def for_canonical(f):
        return lambda k: f(l.canonical(k))

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse(HOTKEY),
        on_activate
    )

    with keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)
    ) as l:
        l.join()


# -------- Tray Icon Menu --------
def quit_app(icon, _item):
    print("👋 Exiting CopyCat...")
    if icon:
        try:
            icon.stop()
        except (AttributeError, RuntimeError):
            pass
    sys.exit(0)


def run_tray():
    global ICON_INSTANCE
    
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "copycat_icon.ico")
        icon_image = Image.open(icon_path)
    except (FileNotFoundError, IOError, OSError):
        icon_size = (64, 64)
        icon_image = Image.new("RGBA", icon_size, color=(0, 0, 0, 0))
        
        draw = ImageDraw.Draw(icon_image)
        
        draw.ellipse([(4, 4), (60, 60)], fill=(70, 130, 180))
        
        draw.ellipse([(12, 16), (36, 48)], fill=(255, 255, 255))
        draw.rectangle([(12, 28), (24, 48)], fill=(70, 130, 180))
        
        draw.ellipse([(28, 28), (52, 60)], fill=(255, 255, 255))
        draw.rectangle([(28, 40), (40, 60)], fill=(70, 130, 180))
    
    ICON_INSTANCE = Icon("CopyCat", icon_image, menu=Menu(MenuItem('Quit CopyCat', quit_app)))
    
    print("🐱 CopyCat is running in the system tray")
    
    try:
        ICON_INSTANCE.run()
    except KeyboardInterrupt:
        print("👋 Exiting CopyCat due to keyboard interrupt...")
        quit_app(ICON_INSTANCE, None)
    except Exception as e:
        print(f"Error in tray icon: {e}")
        if ICON_INSTANCE:
            try:
                ICON_INSTANCE.stop()
            except (AttributeError, RuntimeError):
                pass
        sys.exit(1)


# -------- Main Entrypoint --------
if __name__ == "__main__":
    if not ensure_single_instance():
        print("🐱 CopyCat is already running! Exiting this instance.")
        sys.exit(0)
    
    print(f"🐱 CopyCat is running in the tray. Press {HOTKEY} to type clipboard.")
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    run_tray()
