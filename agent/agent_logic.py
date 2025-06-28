import os
import time
import pyautogui
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import base64

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