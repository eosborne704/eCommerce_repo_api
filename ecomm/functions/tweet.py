import json
from requests_oauthlib import OAuth1Session

class Tweet:
    _instance = None
    CONSUMER_KEY = "YOUR_KEY"
    CONSUMER_SECRET = "YOUR_SECRET"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Tweet, cls).__new__(cls)
            cls._instance.authenticate()
        return cls._instance

    def authenticate(self):
        self.oauth = None # Placeholder for OAuth1Session instance
        pass

    def make_tweet(self, tweet_content):
        if self.oauth:
            response = self.oauth.post("https://api.twitter.com/2/tweets", json=tweet_content)
            if response.status_code != 201:
                raise Exception(f"Error: {response.status_code} {response.text}")
            return response.json()
        else:
            raise Exception("OAuth session not initialized.")
