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
        prompt = """
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
        else:
            print("Did not receive a response from Gemini.")


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