import os
import time
import shutil
import modules.twitch.clip_fetch as clip_fetch
import modules.video.shorts as shorts
import modules.youtube.youtube as youtube
import modules.twitch.clip_download as clip_download
import modules.twitch.vod_fetch as vod_fetch
import modules.util.webhooks as webhooks
import modules.video.vod as vod
from modules.util.sanitization import sanitize_path

def create_short():
    try:
        tags = youtube.load_tags('modules/util/video_tags.json')
        clip = clip_fetch.retrieve_clip()  
        directory = f'content/products/{sanitize_path(clip.title)}'
        
        shorts.generate_video(clip)
        video_id = youtube.upload_video(
            f'{directory}/product.mp4',
            clip.title + " #shorts #clips",
            "Featured streamer: " + clip.broadcaster_name + "\n\nSubscribe for more content like this!",
            tags,
            '24',
            'private'
        )
        webhooks.success(f'Type: YouTube Short\nTitle: {clip.title + " #shorts #clips"}\nVideo link: https://www.youtube.com/watch?v={video_id}')
        if os.path.exists(directory):
            shutil.rmtree(directory)
        
    except Exception as e:
        webhooks.error("Failed to upload short: " + e)


def create_vod():
    try:
        clip_downloader = clip_download.ClipsDownloader()
        selected_vod = vod_fetch.get_relevant_vod()
        
        clips, vod_title = vod_fetch.get_vod_clips(str(selected_vod))
        video_tags = youtube.load_tags('modules/util/video_tags.json')
        directory = f'content/products/{sanitize_path(vod_title)}'
        
        max_views = -1
        top_clip = None
        for _, data in clips.items():
            if data['view_count'] > max_views:
                max_views = data['view_count']
                top_clip = data
        
        clip_order = 0
        for _, data in clips.items():
            clip_order += 1
            clip_downloader.download_clip(data, "vod", vod_title, str(clip_order))
            time.sleep(1)
        
        vod.generate_video(f'content/products/{sanitize_path(vod_title)}')
        video_id = youtube.upload_video(
            f'{directory}/product.mp4',
            top_clip['title'] + ' | ' + top_clip['broadcaster_name'] + ' stream highlights',
            top_clip['broadcaster_name'] + ' stream highlights\n\nSubscribe for more content like this!\nAll credits go to the original creator.\nFind them on Twitch @' + top_clip['broadcaster_name'] + '.',
            video_tags,
            '24',
            'private'
        )
        webhooks.success(f"Type: VOD Highlights\nTitle: {top_clip['title'] + ' (' + top_clip['broadcaster_name'] + ' stream highlights)'}\nVideo link: https://www.youtube.com/watch?v={video_id}")
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    except Exception as e:
        webhooks.error("Failed to upload VOD highlight: " + e)

create_vod()