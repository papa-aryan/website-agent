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
        self.screenshot = None
        print("WebAgent initialized.")

    def take_screenshot(self):
        """
        Takes a screenshot of the entire screen and stores it.
        """
        print("Taking a screenshot...")
        self.screenshot = pyautogui.screenshot()
        # For verification, let's save the image. This line can be removed later.
        self.screenshot.save("screenshot.png")
        print("Screenshot taken and saved as 'screenshot.png'.")
        
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


def main():
    """
    Main function to create and run the AI agent.
    """
    agent = WebAgent()
    agent.run()


if __name__ == "__main__":
    main()