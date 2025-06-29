import os
import time
import pyautogui
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import base64
import json

class WebAgent:
    def __init__(self):
        """
        Initializes the WebAgent, loading credentials and configuring the AI model.
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Please check your .env file.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        self.screenshot = None
        print("WebAgent initialized!!")

    def take_screenshot(self):
        """
        Takes a screenshot of the entire screen and stores it.
        """
        print("Taking a screenshot...")
        self.screenshot = pyautogui.screenshot()
        # For verification, let's save the image. This line can be removed later.
        self.screenshot.save("screenshot.png")
        print("Screenshot taken and saved as 'screenshot.png'.")

    def get_screenshot_as_gemini_part(self):
        """
        Converts the stored screenshot into a Gemini-friendly format.
        """
        if not self.screenshot:
            print("No screenshot available to convert.")
            return None

        print("Converting screenshot for Gemini...")
        # Create an in-memory byte stream
        buffered = BytesIO()
        self.screenshot.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        #print(img_bytes)

        # The Gemini API requires a Part object
        return {
            "mime_type": "image/png",
            "data": img_bytes
        }
    
    def ask_gemini_about_image(self, image_part, prompt):
        """
        Sends the image and a prompt to the Gemini model and gets a response.
        """
        if not image_part:
            print("Cannot ask Gemini without an image.")
            return None
        
        print("Asking Gemini to analyze the screenshot...")
        try:
            response = self.model.generate_content([prompt, image_part])
            return response.text
        except Exception as e:
            print(f"An error occurred while calling Gemini API: {e}")
            return None
            
    def parse_and_process_response(self, response_text, screen_size):
        """
        Parses the JSON response from Gemini and converts normalized coordinates to pixel coordinates.
        """
        print("Parsing and processing Gemini's response...")
        try:
            # Clean the response in case it's wrapped in markdown
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            
            data = json.loads(response_text)
            elements = data.get("elements", [])
            
            screen_width, screen_height = screen_size
            
            for element in elements:
                box = element.get("box_2d")
                if box and len(box) == 4:
                    # Assuming box is [x_min, y_min, x_max, y_max] on a 0-1000 scale
                    norm_x_min, norm_y_min, norm_x_max, norm_y_max = box
                    pixel_x_min = int((norm_x_min / 1000) * screen_width)
                    pixel_y_min = int((norm_y_min / 1000) * screen_height)
                    pixel_x_max = int((norm_x_max / 1000) * screen_width)
                    pixel_y_max = int((norm_y_max / 1000) * screen_height)
                    
                    element["pixel_box"] = [pixel_x_min, pixel_y_min, pixel_x_max, pixel_y_max]
            
            return elements
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing or processing response: {e}")
            print(f"Raw response was: {response_text}")
            return []
        
    def perform_action(self, element, text_to_type=None):
        """
        Performs an action (click or type) on a given UI element.
        """
        if "pixel_box" not in element:
            print(f"Cannot perform action on element with no coordinates: {element.get('label')}")
            return

        pixel_box = element["pixel_box"]
        # Calculate the center of the bounding box
        center_x = (pixel_box[0] + pixel_box[2]) // 2
        center_y = (pixel_box[1] + pixel_box[3]) // 2

        element_type = element.get("type")
        element_label = element.get("label")

        print(f"Performing action on '{element_label}' at ({center_x}, {center_y})...")

        if element_type in ["button", "link"]:
            pyautogui.click(center_x, center_y)
            print("Action: Clicked.")
        elif element_type == "input":
            pyautogui.click(center_x, center_y)
            if text_to_type:
                pyautogui.typewrite(text_to_type, interval=0.05)
                print(f"Action: Typed '{text_to_type}'.")
            else:
                print("Action: Clicked input field, but no text was provided to type.")
        else:
            print(f"Unknown element type: {element_type}")

    def run(self):
        """
        The main execution loop for the agent.
        """
        print("Agent starting in 5 seconds...")
        print("Please open and focus the browser window on the website.")
        time.sleep(5)
        print("Agent is now active.")

        # --- Step 4: Take a Screenshot ---
        self.take_screenshot()

        # --- Step 5: Convert Screenshot for Gemini ---
        image_part = self.get_screenshot_as_gemini_part()
        if image_part:
            print("Screenshot converted and ready for Gemini.")
        if not image_part:
            print("Agent run failed: Could not prepare screenshot.")
            return
        
        # --- Step 6: Send to Gemini with a Prompt ---
        screen_width, screen_height = pyautogui.size()
        prompt = f"""
        Analyze the screenshot of the web page. The screen resolution is {screen_width}x{screen_height}.
        Your task is to identify all interactive elements, including buttons, links, and text input fields.

        Provide the output as a JSON object with a single key "elements".
        The value of "elements" should be a list of objects. Each object must have:
        1. "label": The text content or a short description of the element (e.g., "Submit Information", "Your Name").
        2. "type": The type of element, which must be one of the following strings: "button", "link", or "input".
        3. "box_2d": The bounding box coordinates as a list of four numbers [x_min, y_min, x_max, y_max].

        Return only the raw JSON object, without any surrounding text, explanations, or markdown formatting.
        """
        print("Prompting Gemini...")
        gemini_response = self.ask_gemini_about_image(image_part, prompt)
        
        if gemini_response:
            print("\n--- Gemini Response ---")
            print(gemini_response)
            print("-----------------------\n")
        if not gemini_response:
            print("Did not receive a response from Gemini. Aborting.")
            return

        # --- Step 7: Parse Response and Get Coordinates ---
        interactive_elements = self.parse_and_process_response(gemini_response, (screen_width, screen_height))

        if interactive_elements:
            print("\n--- Identified Interactive Elements (with Pixel Coords) ---")
            for element in interactive_elements:
                print(element)
            print("----------------------------------------------------------\n")
        else:
            print("Could not identify any interactive elements from the response.")

        # --- Step 8: Decide and Perform Action ---
        print("\n--- Identified Interactive Elements ---")
        for i, element in enumerate(interactive_elements):
            print(f"{i+1}: Label='{element.get('label')}', Type='{element.get('type')}'")
        print("-------------------------------------\n")

        try:
            choice_str = input("Enter the number of the element to interact with (or 'q' to quit): ")
            if choice_str.lower() == 'q':
                print("Quitting.")
                return

            choice = int(choice_str) - 1
            if 0 <= choice < len(interactive_elements):
                print("Action will be performed in 3 seconds...")
                time.sleep(3)
                chosen_element = interactive_elements[choice]
                
                text_to_type = None
                if chosen_element.get("type") == "input":
                    text_to_type = input("Enter the text to type into the field: ")

                self.perform_action(chosen_element, text_to_type)
                
                print("\nAction completed. Pausing for 2 seconds to observe result...")
                time.sleep(2)
                print("Agent run finished.")

            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def main():
    """
    Main function to create and run the AI agent.
    """
    agent = WebAgent()

    #print("Available models:")
    #for m in genai.list_models():
    #    if 'generateContent' in m.supported_generation_methods:
    #        print(m.name)

    agent.run()


if __name__ == "__main__":
    main()