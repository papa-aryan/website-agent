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
            os.remove("screenshot.png")

    def test_take_screenshot(self):
        """
        Tests the take_screenshot method.
        """
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


if __name__ == '__main__':
    unittest.main()