import unittest
import os
from PIL import Image
from agent_logic import WebAgent


class TestWebAgent(unittest.TestCase):
    """
    Test suite for the WebAgent class.
    """

    def setUp(self):
        """
        This method runs before each test. 
        It sets up a clean state.
        """
        self.agent = WebAgent()
        # Ensure no old screenshot file exists before the test runs
        if os.path.exists("screenshot.png"):
            os.remove("screenshot.png")

    def tearDown(self):
        """
        This method runs after each test.
        It cleans up any files created during the test.
        """
        if os.path.exists("screenshot.png"):
            print("\n[Debug] Cleaning up screenshot.png in tearDown method...")
            os.remove("screenshot.png")

    def test_take_screenshot(self):
        """
        Tests the take_screenshot method.
        """
        print("\n[Debug] Starting test_take_screenshot...")
        # 1. Verify initial state
        self.assertIsNone(self.agent.screenshot)
        self.assertFalse(os.path.exists("screenshot.png"))

        # 2. Call the method to be tested
        self.agent.take_screenshot()

        # 3. Assert the results
        # Check that the screenshot attribute is now a PIL Image object
        self.assertIsNotNone(self.agent.screenshot)
        self.assertIsInstance(self.agent.screenshot, Image.Image)

        # Check that the screenshot file was created on disk
        self.assertTrue(os.path.exists("screenshot.png"))

    def test_get_screenshot_as_gemini_part_success(self):
        """
        Tests that the screenshot is correctly converted to a Gemini Part.
        """
        print("\n[Debug] Starting test_get_screenshot_as_gemini_part_success...")
        # 1. Setup: Take a screenshot first
        self.agent.take_screenshot()
        self.assertIsNotNone(self.agent.screenshot)

        # 2. Call the method to be tested
        image_part = self.agent.get_screenshot_as_gemini_part()

        # 3. Assert the results
        self.assertIsNotNone(image_part)

        if image_part:
            self.assertIsInstance(image_part, dict)
            self.assertEqual(image_part["mime_type"], "image/png")
            self.assertIsInstance(image_part["data"], bytes)
            self.assertGreater(len(image_part["data"]), 0) # Ensure the byte data is not empty

    def test_get_screenshot_as_gemini_part_no_screenshot(self):
        """
        Tests that the method returns None if no screenshot has been taken.
        """
        print("\n[Debug] Starting test_get_screenshot_as_gemini_part_no_screenshot...")
        # 1. Verify initial state
        self.assertIsNone(self.agent.screenshot)

        # 2. Call the method
        image_part = self.agent.get_screenshot_as_gemini_part()

        # 3. Assert the result
        self.assertIsNone(image_part)


if __name__ == '__main__':
    unittest.main()