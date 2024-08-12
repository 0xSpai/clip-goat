import requests
import pytz
import modules.util.auth as auth
from datetime import datetime, timedelta

vod_id = "2220721446"

headers = {
    'Client-ID': auth.client_id,
    'Authorization': f'Bearer {auth.access_token}'
}

vod_response = requests.get(f'https://api.twitch.tv/helix/videos?id={vod_id}', headers=headers)
vod_data = vod_response.json()['data'][0]

start_time = datetime.fromisoformat(vod_data['created_at'].replace('Z', '+00:00'))
h, m, s = [int(x) if x else 0 for x in vod_data['duration'].replace('h', ':').replace('m', ':').replace('s', '').split(':')]
end_time = start_time + timedelta(hours=h, minutes=m, seconds=s)

url = 'https://api.twitch.tv/helix/clips'
params = {
    'broadcaster_id': vod_data["user_id"],
    'started_at': (datetime.now(pytz.utc) - timedelta(days=14)).isoformat(),
    'ended_at': datetime.now(pytz.utc).isoformat()
}

clips = []
pagination_cursor = None
page_count = 0
max_pages = 10

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
    if start_time <= clip_created_at <= end_time:
        filtered_clips.append(clip)

sorted_clips = sorted(filtered_clips, key=lambda x: datetime.fromisoformat(x['created_at'].rstrip('Z') + '+00:00'), reverse=False)

if sorted_clips:
    for clip in sorted_clips:
        created_at = datetime.fromisoformat(clip['created_at'].rstrip('Z') + '+00:00').strftime('%Y-%m-%d %H:%M:%S')
        print(f"Title: {clip['title']}")
        print(f"URL: {clip['url']}")
        print(f"Created At: {created_at}")
        print()
else:
    print("No clips found from that VOD.")
