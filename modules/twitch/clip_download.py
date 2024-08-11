import requests
import os
from modules.twitch.twitch_api import TwitchAPI
from modules.util.auth import client_id, client_secret

api = TwitchAPI()
api.auth(client_id, client_secret)

class ClipContent:
    def __init__(self, url, broadcaster_id, broadcaster_name, game_id, title, thumbnail_url, duration, path, language):
        self.url = url
        self.broadcaster_id = broadcaster_id
        self.broadcaster_name = broadcaster_name
        self.game_id = game_id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.duration = duration
        self.path = path
        self.language = language
    
    def __str__(self):
        return (f'url: {self.url}\nbroadcaster_id: {self.broadcaster_id}\n'
                f'broadcaster_name: {self.broadcaster_name}\ngame_id: {self.game_id}\n'
                f'title: {self.title}\nthumbnail_url: {self.thumbnail_url}\n'
                f'duration: {self.duration}\nlanguage: {self.language}')

class ClipsExtractor:
    def get_clip_by_id(self, clip_id):
        params = {'id': clip_id}
        response = requests.get('https://api.twitch.tv/helix/clips', params=params, headers=api.headers).json()
        clip_data = response['data'][0] if 'data' in response and response['data'] else None
        if clip_data:
            return ClipContent(
                clip_data['url'],
                clip_data['broadcaster_id'],
                clip_data['broadcaster_name'],
                clip_data['game_id'],
                clip_data['title'],
                clip_data['thumbnail_url'],
                clip_data['duration'],
                f'content/raw_clips/{clip_data["title"].replace(" ", "_").replace("/", "_").lower()}.mp4',
                clip_data['language']
            )
        return None
        
class ClipsDownloader:
    def download_clip(self, clip):
        index = clip.thumbnail_url.find('-preview')
        clip_url = clip.thumbnail_url[:index] + '.mp4'

        r = requests.get(clip_url, stream=True)
        if r.status_code == 200:
            directory = f'content/shorts/{clip.title.replace(" ", "_").replace("/", "_").lower()}'
            if not os.path.exists(directory):
                os.makedirs(directory)

            file_path = os.path.join(directory, 'raw_clip.mp4')
            
            with open(file_path, 'wb') as f:
                f.write(r.content)
            
            return directory
        else:
            print(f'Failed to download clip from URL: {clip_url}')
            return None

    def download_thumbnail(self, clip):
        directory = f'content/shorts/{clip.title.replace(" ", "_").replace("/", "_").lower()}'
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        r = requests.get(clip.thumbnail_url)
        if r.status_code == 200:
            thumbnail_path = os.path.join(directory, 'thumbnail.jpg')
            
            try:
                with open(thumbnail_path, 'wb') as f:
                    f.write(r.content)
            except IOError:
                print(f'Failed to save thumbnail: {thumbnail_path}')
        else:
            print(f'Failed to download thumbnail from URL: {clip.thumbnail_url}')
    
def extract_clip_id(clip_url):
    return clip_url.split('/')[-1]
