import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import pickle

CLIENT_SECRETS_FILE = 'modules/youtube/google_api.json'
CREDENTIALS_FILE = 'modules/youtube/token.pickle'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    credentials = None

    # Load credentials from file if it exists
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'rb') as token:
                credentials = pickle.load(token)
        except EOFError:
            print(f"File {CREDENTIALS_FILE} is empty or corrupted.")
        except pickle.UnpicklingError:
            print(f"File {CREDENTIALS_FILE} is not a valid pickle file.")
        except Exception as e:
            print(f"Error reading {CREDENTIALS_FILE}: {e}")

    # If credentials are not available or invalid, perform OAuth2 flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                credentials = None
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                credentials = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error during OAuth2 flow: {e}")
                raise
        # Save the credentials for the next run
        try:
            with open(CREDENTIALS_FILE, 'wb') as token:
                pickle.dump(credentials, token)
        except Exception as e:
            print(f"Error saving {CREDENTIALS_FILE}: {e}")
            raise

    return build('youtube', 'v3', credentials=credentials)

def upload_video(file_path, title, description, tags, category_id, status):
    try:
        media_file = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': status
            }
        }
        
        request = get_authenticated_service().videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media_file
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        
        print(f"Upload complete! Video link: https://www.youtube.com/shorts/{response['id']}")
        return response['id']
    
    except Exception as e:
        print(f"An error occurred: {e}")

def load_tags(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data.get('tags', [])