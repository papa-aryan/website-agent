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
            raise ValueError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        self.screenshot = None
        self.history = []
        self.max_iterations = 10
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
        
    def ask_gemini_text_only(self, prompt):
        """
        Sends a text-only prompt to the Gemini model.
        """
        print("Asking Gemini a text-only question...")
        try:
            # Note: We only pass the prompt, no image part.
            response = self.model.generate_content(prompt)
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

    def construct_prompt(self, screen_width, screen_height):
        """
        Constructs the prompt for the Gemini model, including history.
        """
        history_str = "\n".join(self.history)
        return f"""
Analyze the screenshot of the web page. The screen resolution is {screen_width}x{screen_height}.
The user's objective is: {self.history[0]}
The history of my previous actions is:
{history_str}

Based on the user's objective and the history, your task is to identify ALL interactive elements that could help achieve the objective.
These elements include buttons, links, and text input fields.

Provide the output as a JSON object with a single key "elements".
The value of "elements" should be a list of objects. Each object must have:
1. "label": The text content or a short description of the element (e.g., "Submit Information", "Your Name").
2. "type": The type of element, which must be one of the following strings: "button", "link", or "input".
3. "box_2d": The bounding box coordinates as a list of four numbers [x_min, y_min, x_max, y_max].

Return only the raw JSON object, without any surrounding text, explanations, or markdown formatting.
"""

    def decide_next_action(self, interactive_elements):
        """
        Asks the Gemini model to decide the next action to take.
        """
        prompt = f"""
My main objective is: {self.history[0]}

Here are the interactive elements I've identified on the current screen:
{json.dumps(interactive_elements, indent=2)}

My action history so far is:
{"\n".join(self.history)}

Your task is to choose the best element to interact with to get closer to achieving the main objective.
Review the action history carefully. Has the objective already been accomplished in a previous step?
The objective may require multiple steps and navigating through different pages (like a search function).
Think step-by-step. If you don't see an element that directly accomplishes the objective, choose one that is a logical step towards it (e.g., a 'Next' button, a relevant link like 'Buttons Page', or a menu). If you get stuck, you can usually return to the homepage too to start over and explore a different branch.

Please provide your response as a JSON object with two keys:
1. "thought": A brief explanation of your reasoning.
2. "chosen_element_label": The exact label of the element you've chosen from the list above.

Example:
{{
  "thought": "To find the 'About' page, clicking the 'Menu' button seems like the most logical next step.",
  "chosen_element_label": "Menu"
}}

If you think the objective has been met, please return an empty JSON object.
Return only the raw JSON object.
"""
        print("Asking Gemini to decide on the next action...")
        response_text = self.ask_gemini_text_only(prompt)

        if not response_text:
            return None, None

        print("\n--- Gemini Decision ---")
        print(response_text)
        print("-----------------------\n")

        try:
            if response_text.strip().startswith("```json"):
                response_text = response_text.strip()[7:-3].strip()
            
            decision_data = json.loads(response_text)
            if not decision_data: # Empty object means goal is met
                return None, "Objective achieved."

            thought = decision_data.get("thought")
            chosen_label = decision_data.get("chosen_element_label")

            for element in interactive_elements:
                if element.get("label") == chosen_label:
                    return element, thought
            
            return None, "Could not find the chosen element."

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing decision response: {e}")
            print(f"Raw response was: {response_text}")
            return None, None

    def run(self, user_prompt):
        """
        The main execution loop for the agent.
        """
        print("Agent starting in 5 seconds...")
        print("Please open and focus the browser window on the website.")
        time.sleep(5)
        print("Agent is now active.")

        self.history.append(f"User's objective: {user_prompt}")

        for i in range(self.max_iterations):
            print(f"--- Iteration {i+1} ---")

            # --- Step 1: Take a Screenshot ---
            self.take_screenshot()

            # --- Step 2: Convert Screenshot for Gemini ---
            image_part = self.get_screenshot_as_gemini_part()
            if not image_part:
                print("Agent run failed: Could not prepare screenshot.")
                return

            # --- Step 3: Send to Gemini with a Prompt ---
            screen_width, screen_height = pyautogui.size()
            
            print("\n--- History for Gemini ---")
            for item in self.history:
                print(item)
            print("--------------------------\n")
            
            prompt = self.construct_prompt(screen_width, screen_height)
            
            print("Prompting Gemini...")
            gemini_response = self.ask_gemini_about_image(image_part, prompt)
            
            if gemini_response:
                print("\n--- Gemini Response ---")
                print(gemini_response)
                print("-----------------------\n")
            if not gemini_response:
                print("Did not receive a response from Gemini. Aborting.")
                return

            # --- Step 4: Parse Response and Get Coordinates ---
            interactive_elements = self.parse_and_process_response(gemini_response, (screen_width, screen_height))

            if not interactive_elements:
                print("Could not identify any interactive elements from the response. Ending run.")
                return

            # --- Step 5: Decide and Perform Action ---
            chosen_element, thought = self.decide_next_action(interactive_elements)

            if chosen_element:
                # Add structured history entries
                history_entry = f"Iteration {i+1}: \nThought: {thought}\nAction: "
                
                text_to_type = None
                if chosen_element.get("type") == "input":
                    # For now, we'll just use a placeholder. This can be improved later.
                    text_to_type = "hello world"
                    history_entry += f"Typing '{text_to_type}' into '{chosen_element.get('label')}'."
                else:
                    history_entry += f"Clicking '{chosen_element.get('label')}'."

                self.history.append(history_entry)

                self.perform_action(chosen_element, text_to_type)
                
                print("\nAction completed. Pausing for 2 seconds to observe result...")
                time.sleep(2)
            else:
                print("Gemini could not decide on an action. Ending run.")
                return

        print("Maximum iterations reached. Ending agent run.")


def main():
    """
    Main function to create and run the AI agent.
    """
    agent = WebAgent()

    #print("Available models:")
    #for m in genai.list_models():
    #    if 'generateContent' in m.supported_generation_methods:
    #        print(m.name)

    user_prompt = input("Please tell me what you want to do on the website: ")
    agent.run(user_prompt)


if __name__ == "__main__":
    main()