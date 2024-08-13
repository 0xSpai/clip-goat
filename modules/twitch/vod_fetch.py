import json
import requests
import random
import pytz
from modules.twitch.twitch_api import TwitchAPI
from datetime import datetime, timedelta
from modules.util.auth import client_id, client_secret, access_token
from modules.util.sanitization import sanitize_path

api = TwitchAPI()
api.auth(client_id, client_secret)

streamers = [
    'caseoh_', 'KaiCenat', 'hasanabi', 'Jynxzi', 'tarik', 'plaqueboymax',
    'jasontheween', 'xQc', 'Clix', 'Agent00', 'stableronaldo', 'PirateSoftware',
    'Fanum', 'Emiru', 'madisonbeer', 'Mizkif', 'ironmouse', 'CDawgVA'
]

def get_clips_dictionary(clips):
    clips_dict = {}
    
    if clips:
        for i, clip in enumerate(clips):
            clips_dict[f"clip_{i+1}"] = clip
    else:
        return "Could not find any clips from that VOD."

    return clips_dict

def get_relevant_vod():
    attempts = 0
    while attempts < 5:
        try:
            username = random.choice(streamers)
            response = requests.get(f'https://api.twitch.tv/helix/users?login={username}', headers=api.headers)
            response.raise_for_status()
            user_id = response.json()['data'][0]['id']

            response = requests.get(f'https://api.twitch.tv/helix/videos?user_id={user_id}&sort=time&type=archive', headers=api.headers)
            response.raise_for_status()
            vods = response.json().get('data', [])

            with open("content/vod_history.json", 'r') as file:
                vod_history = json.load(file)
            seven_days = datetime.utcnow() - timedelta(days=7)

            found_vod = False
            for vod in vods:
                vod_date = datetime.strptime(vod['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                if vod_date > seven_days:
                    sanitized_title = sanitize_path(vod['title'])
                    if sanitized_title not in vod_history:
                        vod_history.append(sanitized_title)
                        with open("content/vod_history.json", 'w') as file:
                            json.dump(vod_history, file, indent=4)

                    found_vod = True
                    return vod["url"].split('/')[-1]

            if found_vod:
                break
            else:
                print("No applicable VODs found. Trying again...")
                attempts += 1

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            attempts += 1

    if attempts == 5:
        return None
    
def get_vod_clips(vod_id):
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }

    vod_response = requests.get(f'https://api.twitch.tv/helix/videos?id={vod_id}', headers=headers)
    vod_data = vod_response.json()['data'][0]

    start_time = datetime.fromisoformat(vod_data['created_at'].replace('Z', '+00:00'))
    h, m, s = [int(x) if x else 0 for x in vod_data['duration'].replace('h', ':').replace('m', ':').replace('s', '').split(':')]
    end_time = start_time + timedelta(hours=h, minutes=m, seconds=s)

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
                'view_count': clip['view_count'],
                'thumbnail_url': clip['thumbnail_url']
            })

    sorted_clips = sorted(filtered_clips, key=lambda x: x['start'])
    
    non_overlapping_clips = []
    last_end_time = None

    for clip in sorted_clips:
        if last_end_time is None or clip['start'] >= last_end_time:
            non_overlapping_clips.append(clip)
            last_end_time = clip['end']
        else:
            for i in range(len(non_overlapping_clips)):
                if non_overlapping_clips[i]['end'] > clip['start'] and clip['view_count'] > non_overlapping_clips[i]['view_count']:
                    non_overlapping_clips.pop(i)
                    non_overlapping_clips.append(clip)
                    last_end_time = clip['end']
                    break
            else:
                if clip['end'] <= last_end_time:
                    continue
                non_overlapping_clips.append(clip)
                last_end_time = clip['end']

    total_duration = timedelta()
    target_duration_minutes = random.randint(9, 20)

    for clip in non_overlapping_clips:
        total_duration += clip['duration']

    total_duration_minutes = total_duration.total_seconds() / 60

    if total_duration_minutes > target_duration_minutes:
        while total_duration_minutes > target_duration_minutes and non_overlapping_clips:
            least_duration_clip = min(non_overlapping_clips, key=lambda x: x['duration'])
            non_overlapping_clips.remove(least_duration_clip)
            total_duration -= least_duration_clip['duration']
            total_duration_minutes = total_duration.total_seconds() / 60

    return get_clips_dictionary(non_overlapping_clips), vod_data['title']