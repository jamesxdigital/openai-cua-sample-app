from computers import Computer
from utils import (
    create_response,
    show_image,
    pp,
    sanitize_message,
    check_blocklisted_url,
)
import json
from typing import Callable
import time


class Agent:
    """
    A sample agent class that can be used to interact with a computer.

    (See simple_cua_loop.py for a simple example without an agent.)
    """

    def __init__(
        self,
        model="computer-use-preview",
        computer: Computer = None,
        tools: list[dict] = [],
        acknowledge_safety_check_callback: Callable = lambda: False,
    ):
        self.model = model
        self.computer = computer
        self.tools = tools
        self.print_steps = True
        self.debug = False
        self.show_images = False
        self.acknowledge_safety_check_callback = acknowledge_safety_check_callback

        if computer:
            self.tools += [
                {
                    "type": "computer-preview",
                    "display_width": computer.dimensions[0],
                    "display_height": computer.dimensions[1],
                    "environment": computer.environment,
                },
            ]

    def debug_print(self, *args):
        if self.debug:
            pp(*args)

    def handle_item(self, item):
        """Handle each item; may cause a computer action + screenshot."""
        if item["type"] == "message":
            if self.print_steps:
                print(item["content"][0]["text"])

        if item["type"] == "function_call":
            name, args = item["name"], json.loads(item["arguments"])
            if self.print_steps:
                print(f"{name}({args})")

            if hasattr(self.computer, name):  # if function exists on computer, call it
                method = getattr(self.computer, name)
                method(**args)
            return [
                {
                    "type": "function_call_output",
                    "call_id": item["call_id"],
                    "output": "success",  # hard-coded output for demo
                }
            ]

        if item["type"] == "computer_call":
            action = item["action"]
            action_type = action["type"]
            action_args = {k: v for k, v in action.items() if k != "type"}
            if self.print_steps:
                print(f"{action_type}({action_args})")

            # Add debug information
            print(f"Processing computer call with ID: {item['call_id']}")

            try:
                # Get the method from the computer object
                method = getattr(self.computer, action_type)
                
                # Execute the method with the provided arguments
                method(**action_args)
                
                # Add extra delay after drag operations
                if action_type == "drag":
                    print(f"Adding extra delay after drag operation")
                    time.sleep(0.5)  # Additional wait time for drag operations
                
                # Take a screenshot after the operation
                screenshot_base64 = self.computer.screenshot()
                if self.show_images:
                    show_image(screenshot_base64)

                # if user doesn't ack all safety checks exit with error
                pending_checks = item.get("pending_safety_checks", [])
                for check in pending_checks:
                    message = check["message"]
                    if not self.acknowledge_safety_check_callback(message):
                        raise ValueError(
                            f"Safety check failed: {message}. Cannot continue with unacknowledged safety checks."
                        )

                call_output = {
                    "type": "computer_call_output",
                    "call_id": item["call_id"],
                    "acknowledged_safety_checks": pending_checks,
                    "output": {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                    },
                }

                # additional URL safety checks for browser environments
                if self.computer.environment == "browser":
                    current_url = self.computer.get_current_url()
                    check_blocklisted_url(current_url)
                    call_output["output"]["current_url"] = current_url

                print(f"Returning response for call_id: {item['call_id']}")
                return [call_output]
            except Exception as e:
                print(f"Error during computer call ({action_type}): {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Return an error response that the API can understand
                error_message = f"Error during {action_type} operation: {str(e)}"
                call_output = {
                    "type": "computer_call_output",
                    "call_id": item["call_id"],
                    "output": {
                        "type": "error",
                        "error": error_message,
                    },
                }
                print(f"Returning error response for call_id: {item['call_id']}")
                return [call_output]
        return []

    def run_full_turn(
        self, input_items, print_steps=True, debug=False, show_images=False
    ):
        self.print_steps = print_steps
        self.debug = debug
        self.show_images = show_images
        new_items = []
        max_retries = 3
        retry_count = 0

        # keep looping until we get a final response
        while new_items[-1].get("role") != "assistant" if new_items else True:
            self.debug_print([sanitize_message(msg) for msg in input_items + new_items])

            try:
                response = create_response(
                    model=self.model,
                    input=input_items + new_items,
                    tools=self.tools,
                    truncation="auto",
                )
                self.debug_print(response)

                if "output" not in response:
                    if retry_count < max_retries:
                        retry_count += 1
                        print(f"No output in response. Retrying ({retry_count}/{max_retries})...")
                        # Short delay before retrying
                        time.sleep(1)
                        continue
                    else:
                        print("Max retries reached. Response without output:")
                        print(response)
                        
                        # Instead of raising an exception, create a user-friendly message
                        error_info = "Unknown error"
                        if "error" in response and "message" in response["error"]:
                            error_info = response["error"]["message"]
                        
                        error_message = (
                            f"I encountered an issue while processing your request. "
                            f"The system returned an error: {error_info}"
                        )
                        
                        if self.debug:
                            error_message += f"\n\nDiagnostic information:\n{json.dumps(response, indent=2)}"
                        
                        error_message += "\n\nPlease try a different instruction or rephrase your request."
                        
                        # Add this message as an assistant response
                        new_items.append({
                            "role": "assistant",
                            "content": [{"type": "text", "text": error_message}]
                        })
                        return new_items
                else:
                    # Reset retry counter on successful response
                    retry_count = 0
                    new_items += response["output"]
                    for item in response["output"]:
                        new_items += self.handle_item(item)
            except Exception as e:
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"Error during API call: {str(e)}. Retrying ({retry_count}/{max_retries})...")
                    # Short delay before retrying
                    time.sleep(1)
                    continue
                else:
                    print(f"Max retries reached. Last error: {str(e)}")
                    
                    # Create a user-friendly error message
                    error_message = (
                        f"I encountered an issue while processing your request. "
                        f"Error details: {str(e)}"
                    )
                    
                    if self.debug:
                        import traceback
                        error_message += f"\n\nDiagnostic information:\n{traceback.format_exc()}"
                    
                    error_message += "\n\nPlease try a different instruction or rephrase your request."
                    
                    # Add this message as an assistant response
                    new_items.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": error_message}]
                    })
                    return new_items

        return new_items
