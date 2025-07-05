import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from cryptography.fernet import Fernet
from flask import current_app


# --- Encryption Service ---
def get_encryption_suite():
    return Fernet(current_app.config["ENCRYPTION_KEY"])


def encrypt_data(data):
    return get_encryption_suite().encrypt(data.encode("utf-8"))


def decrypt_data(encrypted_data):
    return get_encryption_suite().decrypt(encrypted_data).decode("utf-8")


# --- YouTube Service ---
class YouTubeService:
    def __init__(self, credentials):
        self.service = build("youtube", "v3", credentials=credentials)

    def get_user_channels(self):
        request = self.service.channels().list(part="snippet,contentDetails", mine=True)
        response = request.execute()
        return response.get("items", [])

    def get_latest_comments(self, channel_id, max_results=50):
        # Fetch comments for all videos on a channel
        request = self.service.commentThreads().list(
            part="snippet",
            allThreadsRelatedToChannelId=channel_id,
            maxResults=max_results,
            order="time",  # Get the most recent ones
        )
        response = request.execute()
        return response.get("items", [])


class GeminiService:
    def __init__(self):
        self.api_key = current_app.config["GEMINI_API_KEY"]
        self.api_url = current_app.config["GEMINI_API_URL"]

    def generate_content(self, prompt):
        """
        Generate content using Gemini API
        Args:
            prompt (str): The text prompt to send to Gemini
        Returns:
            dict: The API response containing the generated content
        """
        import requests

        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}", headers=headers, json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
            return None

    def get_text_response(self, prompt):
        """
        Get just the text response from Gemini API
        Args:
            prompt (str): The text prompt to send to Gemini
        Returns:
            str: The generated text response or None if there was an error
        """
        response = self.generate_content(prompt)
        if response and "candidates" in response:
            try:
                return response["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                print(f"Error parsing Gemini response: {e}")
                return None
        return None

    def classify_comment(self, comment_text):
        prompt = f"""
            You are a YouTube Comment Classifier for a professional content creator. Your job is to categorize the following comment into ONE of the following action-based categories:
            - "Reply to Question": The comment is asking a direct, specific question that needs an answer.
            - "Appreciate Fan": The comment contains strong, specific praise, or indicates loyal viewership. It deserves a heart.
            - "Review & Consider": The comment is constructive criticism, a polite disagreement, or a suggestion for improvement. It is not spam but requires careful thought.
            - "Delete Junk": The comment is spam, a scam, hate speech, or irrelevant self-promotion.
            - "Miscellaneous": The comment doesn't fit into any of the above categories or is unclear.

            Analyze the user's comment below and return ONLY the category name in a JSON format in the given format only.

            Comment: {comment_text}

            Your Response:
            {{"category": "YOUR_CHOSEN_CATEGORY"}}
            """
        try:
            import json

            response_text = self.get_text_response(prompt)
            if response_text:
                # Try to parse the JSON response
                try:
                    response_json = json.loads(response_text)
                    category = response_json.get("category")
                    if category:
                        return category
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract category from text
                    if "Reply to Question" in response_text:
                        return "Reply to Question"
                    elif "Appreciate Fan" in response_text:
                        return "Appreciate Fan"
                    elif "Review & Consider" in response_text:
                        return "Review & Consider"
                    elif "Delete Junk" in response_text:
                        return "Delete Junk"

            return "Miscellaneous"
        except Exception as e:
            print(f"Error classifying comment with Gemini: {e}")
            return "Miscellaneous"
