import requests
from datetime import datetime, timedelta
import modules.util.auth as auth

vod_id = "2216983728"

headers = {
    'Client-ID': auth.client_id,
    'Authorization': f'Bearer {auth.access_token}'
}

vod_data = requests.get(f'https://api.twitch.tv/helix/videos?id={vod_id}', headers=headers).json()['data'][0]
start_time = datetime.fromisoformat(vod_data['created_at'].replace('Z', '+00:00'))
h, m, s = [int(x) if x else 0 for x in vod_data['duration'].replace('h', ':').replace('m', ':').replace('s', '').split(':')]
end_time = start_time + timedelta(hours=h, minutes=m, seconds=s)

# Print results
print(f"Start Time: {start_time.isoformat()}")
print(f"End Time: {end_time.isoformat()}")
