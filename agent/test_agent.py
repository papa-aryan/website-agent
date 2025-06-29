import unittest
from unittest.mock import patch, MagicMock
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

    def test_ask_gemini_about_image_no_image(self):
        """
        Tests that the Gemini call is not made if there is no image.
        """
        print("\n[Debug] Starting test_ask_gemini_about_image_no_image...")
        response = self.agent.ask_gemini_about_image(None, "test prompt")
        self.assertIsNone(response)

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ask_gemini_about_image_success(self, mock_generate_content):
        """
        Tests a successful call to the Gemini API using a mock.
        """
        print("\n[Debug] Starting test_ask_gemini_about_image_success...")
        # 1. Setup the mock
        # Create a fake response object with a 'text' attribute
        fake_response = MagicMock()
        fake_response.text = '{"elements": []}'
        mock_generate_content.return_value = fake_response

        # 2. Call the method
        dummy_image_part = {"mime_type": "image/png", "data": b"dummyimagedata"}
        prompt = "test prompt"
        response_text = self.agent.ask_gemini_about_image(dummy_image_part, prompt)

        # 3. Assert the results
        # Check that our mock was called with the right arguments
        mock_generate_content.assert_called_once_with([prompt, dummy_image_part])
        # Check that our method returned the text from the fake response
        self.assertEqual(response_text, '{"elements": []}')

    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ask_gemini_about_image_api_error(self, mock_generate_content):
        """
        Tests the handling of an API error using a mock.
        """
        print("\n[Debug] Starting test_ask_gemini_about_image_api_error...")
        # 1. Setup the mock to raise an exception
        mock_generate_content.side_effect = Exception("API Failure")

        # 2. Call the method
        dummy_image_part = {"mime_type": "image/png", "data": b"dummyimagedata"}
        response = self.agent.ask_gemini_about_image(dummy_image_part, "test prompt")

        # 3. Assert the result
        self.assertIsNone(response)

    def test_parse_and_process_response_success(self):
        """
        Tests successful parsing of a valid JSON response and correct coordinate conversion.
        """
        print("\n[Debug] Starting test_parse_and_process_response_success...")
        response_text = """
        {
            "elements": [
                {
                    "label": "Go to Form",
                    "type": "link",
                    "box_2d": [100, 200, 300, 400]
                }
            ]
        }
        """
        screen_size = (2000, 1000) # Use easy-to-calculate numbers
        
        elements = self.agent.parse_and_process_response(response_text, screen_size)
        
        self.assertEqual(len(elements), 1)
        element = elements[0]
        self.assertIn("pixel_box", element)
        # Expected: x_min = (100/1000)*2000=200, y_min = (200/1000)*1000=200, etc.
        self.assertEqual(element["pixel_box"], [200, 200, 600, 400])

    def test_parse_and_process_response_malformed_json(self):
        """
        Tests that the method returns an empty list for malformed JSON.
        """
        print("\n[Debug] Starting test_parse_and_process_response_malformed_json...")
        response_text = '{"elements": [ "label": "bad json" }'
        elements = self.agent.parse_and_process_response(response_text, (1920, 1080))
        self.assertEqual(elements, [])

    def test_parse_and_process_response_with_markdown(self):
        """
        Tests that the method correctly parses JSON wrapped in markdown.
        """
        print("\n[Debug] Starting test_parse_and_process_response_with_markdown...")
        response_text = """
        ```json
        {
            "elements": [
                {"label": "A button", "type": "button", "box_2d": [500, 500, 600, 600]}
            ]
        }
        ```
        """
        elements = self.agent.parse_and_process_response(response_text, (1000, 1000))
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]["pixel_box"], [500, 500, 600, 600])

    def test_parse_and_process_response_missing_box(self):
        """
        Tests that elements without a 'box_2d' are handled gracefully.
        """
        print("\n[Debug] Starting test_parse_and_process_response_missing_box...")
        response_text = """
        {
            "elements": [
                {"label": "No box here", "type": "link"}
            ]
        }
        """
        elements = self.agent.parse_and_process_response(response_text, (1920, 1080))
        self.assertEqual(len(elements), 1)
        self.assertNotIn("pixel_box", elements[0])

if __name__ == '__main__':
    unittest.main()