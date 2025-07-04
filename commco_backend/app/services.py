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
        prompt = """
            You are a YouTube Comment Classifier. Categorize the following comment into ONE of these categories: 
            \"Needs Action\", \"Quick Acknowledge\", \"Review & Delete\".

            - \"Needs Action\": The comment is a direct question or specific, constructive feedback.
            - \"Quick Acknowledge\": The comment is general praise, a simple reaction, or a short positive statement.
            - \"Review & Delete\": The comment is spam, hate speech, a scam, or irrelevant self-promotion.

            Comment: "{comment_text}"
            Category:
            """
        try:
            category = self.get_text_response(prompt)
            valid_categories = ["Needs Action", "Quick Acknowledge", "Review & Delete"]
            return category if category in valid_categories else "Quick Acknowledge"
        except Exception as e:
            print(f"Error classifying comment with Gemini: {e}")
            return "Quick Acknowledge"
