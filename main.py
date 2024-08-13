import time
import modules.twitch.vod_fetch as vod_fetch
import modules.twitch.clip_download as clip_download
clip_downloader = clip_download.ClipsDownloader()

selected_vod = vod_fetch.get_relevant_vod()
clips, vod_title = vod_fetch.get_vod_clips(str(selected_vod))
clip_order = 0

for clip_key, data in clips.items():
    clip_order += 1
    clip_downloader.download_clip(data, "vod", vod_title, str(clip_order))
    
    time.sleep(1)

print("Finished downloading clips")