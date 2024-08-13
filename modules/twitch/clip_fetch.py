import os
import json
import requests
import random
import modules.twitch.clip_download as clip_download
import modules.util.webhooks as webhooks
from modules.util.auth import client_id, client_secret, access_token
from modules.twitch.twitch_api import TwitchAPI
from datetime import datetime, timedelta

api = TwitchAPI()
api.auth(client_id, client_secret)

def load_clip_ids(filename="content/clip_history.json"):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as file:
        return json.load(file)

def save_clip_id(clip_ids, filename="content/clip_history.json"):
    with open(filename, 'w') as file:
        json.dump(clip_ids, file)

def get_top_games():
    url = 'https://api.twitch.tv/helix/games/top'
    response = requests.get(url, params={'first':100}, headers=api.headers)

    games_id = {}
    for game in response.json()['data']:
        games_id[game['name']] = game['id']

    return games_id

def get_game_clips(token, client_id, game_id, amount, started_at=None, ended_at=None):
    url = 'https://api.twitch.tv/helix/clips'
    headers = {
        'Authorization': f'Bearer {token}',
        'Client-Id': client_id
    }
    params = {
        'game_id': game_id,
        'first': amount
    }
    if started_at:
        params['started_at'] = started_at
    if ended_at:
        params['ended_at'] = ended_at
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        webhooks.error(f"An error occurred: {e}")
        return None
    
def retrieve_clip():
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        time_range = lambda t: t.isoformat() + "Z"

        topics = [509658, 509672]
        selected_topic = random.choice(topics)

        response_data = get_game_clips(
            access_token, client_id, selected_topic, 25,
            started_at=time_range(start_time), ended_at=time_range(end_time)
        )

        if response_data is None or 'data' not in response_data:
            print("Failed to fetch clips data.")
            return None

        clips_extractor = clip_download.ClipsExtractor()
        clips_downloader = clip_download.ClipsDownloader()

        selected_clip_ids = load_clip_ids()

        attempts = 0
        max_attempts = len(response_data["data"])
        while attempts < max_attempts:
            selected_clip = random.choice(response_data["data"])
            clip_id = clip_download.extract_clip_id(selected_clip['url'])

            if clip_id in selected_clip_ids:
                attempts += 1
                continue

            clip = clips_extractor.get_clip_by_id(clip_id)
            if clip.language == "en" and 10 <= clip.duration <= 45:
                print(f"Selected clip: {clip.title}, URL: {clip.url}")
                selected_clip_ids.append(clip_id)
                save_clip_id(selected_clip_ids)
                clips_downloader.download_clip(clip, "short", None, None)
                clips_downloader.download_thumbnail(clip)

                return clip
            else:
                attempts += 1

        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        webhooks.error(f"An error occurred: {e}")
        return None