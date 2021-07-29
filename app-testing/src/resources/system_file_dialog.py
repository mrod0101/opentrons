"""Cross platform automation for system file dialog."""
import platform
from pathlib import Path
import time

# seems to have to be here on 3.7.10 ?
import AppKit  # pylint: disable=W0611 # noqa: F401
import pyautogui


def input_file_source(file_path: Path) -> None:
    """Input into a system file dialog the path to the file."""
    if platform.system() == "Darwin":
        pyautogui.hotkey("command", "shift", "g")
        pyautogui.press("delete")
        pyautogui.write(str(file_path.parent.resolve()))
        pyautogui.press("enter")
        time.sleep(0.3)
        pyautogui.press("right")
        time.sleep(0.3)
        pyautogui.press("enter")
