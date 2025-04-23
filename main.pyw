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
import pyperclip
import pyautogui
from pynput import keyboard
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem


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
    
    try:
        # Try to create and lock a file
        if sys.platform == 'win32':
            # Windows implementation
            try:
                import msvcrt
                LOCK_FILE_HANDLE = open(LOCK_FILE, 'w', encoding='utf-8')
                try:
                    msvcrt.locking(LOCK_FILE_HANDLE.fileno(), msvcrt.LK_NBLCK, 1)
                    # Register cleanup function
                    atexit.register(release_lock)
                    return True
                except IOError:
                    LOCK_FILE_HANDLE.close()
                    return False
            except ImportError:
                return False
        else:
            # Unix implementation
            try:
                import fcntl
                with open(LOCK_FILE, 'w', encoding='utf-8') as lock_file:
                    LOCK_FILE_HANDLE = lock_file
                    try:
                        fcntl.flock(LOCK_FILE_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        # Register cleanup function
                        atexit.register(release_lock)
                        return True
                    except IOError:
                        LOCK_FILE_HANDLE.close()
                        return False
            except ImportError:
                return False
    except Exception:
        # If any error occurs, assume another instance is running
        if LOCK_FILE_HANDLE:
            LOCK_FILE_HANDLE.close()
        return False


def release_lock():
    """
    Releases the lock file when the application exits.
    """
    global LOCK_FILE_HANDLE
    if LOCK_FILE_HANDLE:
        try:
            if sys.platform == 'win32':
                # Windows implementation
                try:
                    import msvcrt
                    try:
                        msvcrt.locking(LOCK_FILE_HANDLE.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                except ImportError:
                    pass
            else:
                # Unix implementation
                try:
                    import fcntl
                    try:
                        fcntl.flock(LOCK_FILE_HANDLE, fcntl.LOCK_UN)
                    except Exception:
                        pass
                except ImportError:
                    pass
            LOCK_FILE_HANDLE.close()
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass
        except Exception:
            pass


# -------- Typing Clipboard Text --------
def type_clipboard_text():
    """
    Types the current clipboard content using PyAutoGUI.
    Waits for TYPING_DELAY seconds before typing to allow switching windows.
    Handles newlines by using Shift+Enter instead of Enter to avoid triggering form submissions.
    """
    try:
        time.sleep(TYPING_DELAY)
        text = pyperclip.paste()
        if not text:
            print("Clipboard is empty")
            return
        
        print("🐱 CopyCat typing clipboard...")
        
        # Split text by newlines and type each line with Shift+Enter instead of regular Enter
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Type the line content
            pyautogui.write(line, interval=TYPING_INTERVAL)
            
            # If not the last line, press Shift+Enter instead of regular Enter
            if i < len(lines) - 1:
                pyautogui.hotkey('shift', 'enter')
        
        print("✓ Clipboard contents typed successfully")
    except Exception as e:
        error_msg = f"Error typing clipboard: {e}"
        print(error_msg)


# -------- Hotkey Setup --------
def start_hotkey_listener():
    """
    Sets up and starts the keyboard hotkey listener.
    Uses pynput to detect the configured hotkey combination.
    """
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
    """
    Quits the CopyCat application.
    """
    print("👋 Exiting CopyCat...")
    if icon:
        try:
            icon.stop()
        except Exception:
            pass
    # Use os._exit instead of sys.exit to avoid the SystemExit exception
    sys.exit(0)


def run_tray():
    """
    Runs the system tray icon.
    """
    global ICON_INSTANCE
    
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "copycat_icon.ico")
        icon_image = Image.open(icon_path)
    except Exception:
        # Create a better fallback icon (stylized "CC" for CopyCat)
        icon_size = (64, 64)
        icon_image = Image.new("RGBA", icon_size, color=(0, 0, 0, 0))
        
        # Draw a circular background
        draw = ImageDraw.Draw(icon_image)
        
        # Background circle
        draw.ellipse([(4, 4), (60, 60)], fill=(70, 130, 180))
        
        # Draw stylized "C" letters for CopyCat
        draw.ellipse([(12, 16), (36, 48)], fill=(255, 255, 255))
        draw.rectangle([(12, 28), (24, 48)], fill=(70, 130, 180))
        
        draw.ellipse([(28, 28), (52, 60)], fill=(255, 255, 255))
        draw.rectangle([(28, 40), (40, 60)], fill=(70, 130, 180))
    
    ICON_INSTANCE = Icon("CopyCat", icon_image, menu=Menu(MenuItem('Quit CopyCat', quit_app)))
    
    print("🐱 CopyCat is running in the system tray")
    
    try:
        ICON_INSTANCE.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("👋 Exiting CopyCat due to keyboard interrupt...")
        quit_app(ICON_INSTANCE, None)
    except Exception as e:
        print(f"Error in tray icon: {e}")
        # Make sure to clean up
        if ICON_INSTANCE:
            try:
                ICON_INSTANCE.stop()
            except Exception:
                pass
        sys.exit(1)


# -------- Main Entrypoint --------
if __name__ == "__main__":
    # Check for existing instance first, before creating any resources
    if not ensure_single_instance():
        print("🐱 CopyCat is already running! Exiting this instance.")
        # Exit immediately without creating any resources
        sys.exit(0)
    
    # If we get here, we're the only instance
    print(f"🐱 CopyCat is running in the tray. Press {HOTKEY} to type clipboard.")
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    run_tray()
