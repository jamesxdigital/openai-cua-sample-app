import time
import base64
from typing import List, Dict, Literal
import pyautogui
import io
from PIL import Image

class MacComputer:
    """
    A computer implementation that controls the Mac OS using PyAutoGUI.
    This allows the agent to control your Mac directly without launching a browser.
    """

    environment: Literal["mac"] = "mac"
    
    # Default screen dimensions - will be updated in __enter__
    dimensions = (3456, 2234)

    def __init__(self):
        self._initialized = False

    def __enter__(self):
        # Get the actual screen size
        screen_width, screen_height = pyautogui.size()
        self.dimensions = (screen_width, screen_height)
        
        # Set PyAutoGUI settings
        pyautogui.FAILSAFE = True  # Move mouse to upper-left corner to abort
        pyautogui.PAUSE = 0  # Add a small pause between PyAutoGUI commands
        
        self._initialized = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._initialized = False

    def screenshot(self) -> str:
        """Take a screenshot and return it as a base64-encoded string."""
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified coordinates."""
        pyautogui.click(x=x, y=y, button=button)

    def double_click(self, x: int, y: int) -> None:
        """Double-click at the specified coordinates."""
        pyautogui.doubleClick(x=x, y=y)

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """Scroll at the specified coordinates."""
        pyautogui.moveTo(x, y)
        pyautogui.scroll(scroll_y)  # PyAutoGUI primarily supports vertical scrolling

    def type(self, text: str) -> None:
        """Type the specified text."""
        pyautogui.typewrite(text)

    def wait(self, ms: int = 1000) -> None:
        """Wait for the specified number of milliseconds."""
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        """Move the mouse to the specified coordinates."""
        pyautogui.moveTo(x, y)

    def keypress(self, keys: List[str]) -> None:
        """Press the specified keys."""
        # Convert keys to PyAutoGUI format if needed
        for key in keys:
            pyautogui.keyDown(key)
        for key in reversed(keys):
            pyautogui.keyUp(key)

    def drag(self, path: List[List[int]]) -> None:
        """Drag the mouse along the specified path."""
        start_point = path[0]
        pyautogui.moveTo(start_point[0], start_point[1])
        pyautogui.mouseDown()
        
        for point in path[1:]:
            pyautogui.moveTo(point[0], point[1])
        
        pyautogui.mouseUp()

    def get_current_url(self) -> str:
        """
        This method is required by the Computer interface but doesn't apply to Mac OS.
        Return an empty string as we're not in a browser.
        """
        return "" 