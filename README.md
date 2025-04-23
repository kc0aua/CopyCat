# CopyCat

CopyCat is a Python desktop utility application that allows you to type the contents of your clipboard using a hotkey. It's particularly useful for applications that don't accept standard paste operations.

## Features
- **Clipboard Typing**: Automatically type the contents of your clipboard with a hotkey (Ctrl+Alt+T by default)
- **System Tray Integration**: Runs quietly in your system tray
- **Error Handling**: Gracefully handles clipboard and typing errors
- **Configurable**: Easy to customize typing speed and hotkey combination
- **Smart Newline Handling**: Uses Shift+Enter instead of Enter to avoid triggering form submissions
- **Single-Instance**: Ensures only one copy of CopyCat runs at a time

## Requirements
- Python 3.6+
- Windows, macOS, or Linux (with GUI support)

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.pyw
   ```

## Usage

1. Start CopyCat (it will appear in your system tray)
2. Copy text to your clipboard (Ctrl+C)
3. Place your cursor where you want to type the text
4. Press Ctrl+Alt+T to automatically type the clipboard contents

## Customization

You can customize CopyCat by editing the following variables at the top of `main.pyw`:

```python
# Configuration
HOTKEY = '<ctrl>+<alt>+t'  # Change to your preferred hotkey
TYPING_DELAY = 0.5         # Seconds to wait before typing begins
TYPING_INTERVAL = 0        # Delay between keystrokes (0 = fastest)
```

## Custom Icon

CopyCat will look for a file named `copycat_icon.ico` in the same directory as the script. If not found, it will generate a simple colored icon.

## Dependencies

- pyperclip - Clipboard access
- pyautogui - Keyboard automation
- pynput - Hotkey detection
- pystray - System tray functionality
- Pillow - Icon handling

## License

MIT
