import time
import base64
from typing import List, Dict, Literal, Union, Any
import pyautogui
import io
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MacComputer')

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
        pyautogui.PAUSE = 0.1  # Add a small pause between PyAutoGUI commands
        
        logger.info(f"Initialized MacComputer with dimensions {self.dimensions}")
        self._initialized = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._initialized = False
        logger.info("Exited MacComputer")

    def screenshot(self) -> str:
        """Take a screenshot and return it as a base64-encoded string."""
        try:
            screenshot = pyautogui.screenshot()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            # Return a simple 1x1 transparent PNG if screenshot fails
            img = Image.new('RGBA', (1, 1), (255, 255, 255, 0))
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()

    def click(self, x: int, y: int, button: str = "left") -> None:
        """Click at the specified coordinates."""
        try:
            logger.info(f"Clicking at ({x}, {y}) with button {button}")
            pyautogui.click(x=x, y=y, button=button)
            time.sleep(0.1)  # Small delay after click
        except Exception as e:
            logger.error(f"Error during click operation: {str(e)}")

    def double_click(self, x: int, y: int) -> None:
        """Double-click at the specified coordinates."""
        try:
            logger.info(f"Double-clicking at ({x}, {y})")
            pyautogui.doubleClick(x=x, y=y)
            time.sleep(0.1)  # Small delay after double-click
        except Exception as e:
            logger.error(f"Error during double-click operation: {str(e)}")

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """Scroll at the specified coordinates."""
        try:
            logger.info(f"Scrolling at ({x}, {y}) with amounts ({scroll_x}, {scroll_y})")
            pyautogui.moveTo(x, y)
            pyautogui.scroll(scroll_y)  # PyAutoGUI primarily supports vertical scrolling
            time.sleep(0.1)  # Small delay after scroll
        except Exception as e:
            logger.error(f"Error during scroll operation: {str(e)}")

    def type(self, text: str) -> None:
        """Type the specified text."""
        try:
            logger.info(f"Typing text: {text}")
            pyautogui.typewrite(text)
            time.sleep(0.1)  # Small delay after typing
        except Exception as e:
            logger.error(f"Error during type operation: {str(e)}")

    def wait(self, ms: int = 1000) -> None:
        """Wait for the specified number of milliseconds."""
        try:
            wait_seconds = ms / 1000
            logger.info(f"Waiting for {wait_seconds} seconds")
            time.sleep(wait_seconds)
        except Exception as e:
            logger.error(f"Error during wait operation: {str(e)}")

    def move(self, x: int, y: int) -> None:
        """Move the mouse to the specified coordinates."""
        try:
            logger.info(f"Moving to ({x}, {y})")
            pyautogui.moveTo(x, y)
            time.sleep(0.1)  # Small delay after move
        except Exception as e:
            logger.error(f"Error during move operation: {str(e)}")

    def keypress(self, keys: List[str]) -> None:
        """Press the specified keys."""
        try:
            logger.info(f"Pressing keys: {keys}")
            # Convert keys to PyAutoGUI format if needed
            for key in keys:
                pyautogui.keyDown(key)
            time.sleep(0.1)  # Small delay between key down and key up
            for key in reversed(keys):
                pyautogui.keyUp(key)
            time.sleep(0.1)  # Small delay after keypress
        except Exception as e:
            logger.error(f"Error during keypress operation: {str(e)}")

    def drag(self, path: Union[List[Dict[str, int]], List[List[int]]]) -> None:
        """
        Drag the mouse along the specified path.
        
        Handles various possible formats:
        - [{'x': x1, 'y': y1}, {'x': x2, 'y': y2}, ...]
        - [[x1, y1], [x2, y2], ...]
        - {'path': [{'x': x1, 'y': y1}, {'x': x2, 'y': y2}, ...]}
        """
        try:
            # Handle the case where path is a dict with a 'path' key
            if isinstance(path, dict) and 'path' in path:
                logger.info("Detected path in dictionary format, extracting path value")
                path = path['path']
            
            logger.info(f"Starting drag operation with path: {path}")
            
            if not path or len(path) < 2:
                logger.error("Drag path must contain at least two points")
                return
                
            # Handle first point based on format
            start_point = path[0]
            if isinstance(start_point, dict) and 'x' in start_point and 'y' in start_point:
                # Format is [{'x': x1, 'y': y1}, ...]
                x, y = start_point['x'], start_point['y']
            elif isinstance(start_point, list) and len(start_point) >= 2:
                # Format is [[x1, y1], ...]
                x, y = start_point[0], start_point[1]
            else:
                logger.error(f"Invalid start point format: {start_point}")
                return
                
            logger.info(f"Moving to start point ({x}, {y})")
            pyautogui.moveTo(x, y)
            time.sleep(0.2)  # Ensure we're at the start position
            
            logger.info("Pressing mouse button down")
            pyautogui.mouseDown()
            time.sleep(0.2)  # Give time for the mouseDown to register
            
            # Process remaining points
            for point in path[1:]:
                if isinstance(point, dict) and 'x' in point and 'y' in point:
                    x, y = point['x'], point['y']
                elif isinstance(point, list) and len(point) >= 2:
                    x, y = point[0], point[1]
                else:
                    logger.error(f"Invalid point format: {point}")
                    continue
                    
                logger.info(f"Dragging to ({x}, {y})")
                pyautogui.moveTo(x, y, duration=0.1)  # Slow down the drag movement
                time.sleep(0.1)  # Small pause at each point
            
            logger.info("Releasing mouse button")
            time.sleep(0.2)  # Give time before mouseUp
            pyautogui.mouseUp()
            time.sleep(0.5)  # Allow time for the system to process the drag
            
            logger.info("Drag operation completed")
        except Exception as e:
            logger.error(f"Error during drag operation: {str(e)}")
            try:
                # Make sure the mouse button is released in case of an error
                pyautogui.mouseUp()
            except:
                pass

    def get_current_url(self) -> str:
        """
        This method is required by the Computer interface but doesn't apply to Mac OS.
        Return an empty string as we're not in a browser.
        """
        return "" 