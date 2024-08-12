import os
import json
import requests
import random
import pytz
import modules.twitch.clip_download as clip_download
import modules.util.embeds as embeds
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

def get_clips_dictionary(clips):
    clips_dict = {}
    
    if clips:
        for i, clip in enumerate(clips):
            clips_dict[f"clip_{i+1}"] = clip['url']
    else:
        return "Could not find any clips from that VOD."

    return clips_dict

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
        embeds.error(f"An error occurred: {e}")
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
                clips_downloader.download_clip(clip)
                clips_downloader.download_thumbnail(clip)

                return clip
            else:
                attempts += 1

        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        embeds.error(f"An error occurred: {e}")
        return None

import requests
from datetime import datetime, timedelta
import pytz
import random

def retrieve_vod_clips(vod_id):
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }

    # Fetch VOD details
    vod_response = requests.get(f'https://api.twitch.tv/helix/videos?id={vod_id}', headers=headers)
    vod_data = vod_response.json()['data'][0]

    start_time = datetime.fromisoformat(vod_data['created_at'].replace('Z', '+00:00'))
    h, m, s = [int(x) if x else 0 for x in vod_data['duration'].replace('h', ':').replace('m', ':').replace('s', '').split(':')]
    end_time = start_time + timedelta(hours=h, minutes=m, seconds=s)

    # Fetch clips
    url = 'https://api.twitch.tv/helix/clips'
    params = {
        'broadcaster_id': vod_data["user_id"],
        'started_at': (datetime.now(pytz.utc) - timedelta(days=7)).isoformat(),
        'ended_at': datetime.now(pytz.utc).isoformat()
    }

    clips = []
    pagination_cursor = None
    page_count = 0
    max_pages = random.randint(10, 20)

    while True:
        if pagination_cursor:
            params['after'] = pagination_cursor

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            clips.extend(data.get('data', []))
            
            if 'pagination' in data and 'cursor' in data['pagination']:
                pagination_cursor = data['pagination']['cursor']
            else:
                break
        
            page_count += 1
            if page_count >= max_pages:
                break
        
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            break

    # Filter clips
    filtered_clips = []
    for clip in clips:
        clip_created_at = datetime.fromisoformat(clip['created_at'].rstrip('Z') + '+00:00')
        clip_duration = timedelta(seconds=int(clip['duration'].split('s')[0])) if isinstance(clip['duration'], str) else timedelta(seconds=clip['duration'])
        
        clip_start = clip_created_at
        clip_end = clip_start + clip_duration
        
        if start_time <= clip_start <= end_time or start_time <= clip_end <= end_time:
            filtered_clips.append({
                'title': clip['title'],
                'url': clip['url'],
                'start': clip_start,
                'end': clip_end,
                'duration': clip_duration,
                'view_count': clip['view_count']
            })

    sorted_clips = sorted(filtered_clips, key=lambda x: x['start'])
    clips = []
    last_clip = None

    for clip in sorted_clips:
        if last_clip is None:
            clips.append(clip)
            last_clip = clip
        else:
            if clip['start'] < last_clip['end']:
                if clip['view_count'] > last_clip['view_count']:
                    clips.pop()
                    clips.append(clip)
                    last_clip = clip
            else:
                clips.append(clip)
                last_clip = clip

    total_duration = timedelta()
    for clip in clips:
        total_duration += clip['duration']

    total_duration_minutes = total_duration.total_seconds() / 60
    target_duration_minutes = random.randint(9, 20)

    if total_duration_minutes > target_duration_minutes:
        clips.sort(key=lambda x: x['view_count'])
        while total_duration_minutes > target_duration_minutes and clips:
            least_viewed_clip = clips.pop(0)
            total_duration -= least_viewed_clip['duration']
            total_duration_minutes = total_duration.total_seconds() / 60

    return(get_clips_dictionary(sorted_clips))