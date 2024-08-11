import requests

class TwitchAPI:
    def __init__(self):
        self.headers = None

    def auth(self, client_id, client_secret):
        url = 'https://id.twitch.tv/oauth2/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as err:
            raise SystemExit(f"Error occurred: {err}")
        
        response_data = response.json()
        if 'access_token' not in response_data:
            raise SystemExit("Access token not found in the response")

        bearer = response_data['access_token']

        self.headers = {
            'Authorization': f'Bearer {bearer}',
            'Client-Id': client_id,
        }

    def make_request(self, endpoint):
        if not self.headers:
            raise SystemExit("Authorization headers not set. Please authenticate first.")
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as err:
            raise SystemExit(f"Error occurred: {err}")