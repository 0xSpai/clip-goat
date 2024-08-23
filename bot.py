import os
import time
import schedule
import shutil
import random
import modules.twitch.clip_fetch as clip_fetch
import modules.video.shorts as shorts
import modules.youtube.youtube as youtube
import modules.twitch.clip_download as clip_download
import modules.twitch.vod_fetch as vod_fetch
import modules.util.webhooks as webhooks
import modules.video.vod as vod
from modules.util.sanitization import sanitize_path

video_tags = youtube.load_tags('modules/util/video_tags.json')

def create_short():
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            clip = clip_fetch.retrieve_clip()
            directory = f'content/output/{sanitize_path(clip.title)}'
            
            shorts.generate_video(clip)
            video_id = youtube.upload_video(
                f'{directory}/product.mp4',
                clip.title + " #shorts #clips",
                "Featured streamer: " + clip.broadcaster_name + "\n\nSubscribe for more content like this!",
                video_tags,
                '24',
                'public'
            )
            webhooks.success(f'Type: YouTube Short\nTitle: {clip.title + " #shorts #clips"}\nVideo link: https://www.youtube.com/watch?v={video_id}')
            if os.path.exists(directory):
                shutil.rmtree(directory)
            
            break

        except Exception as e:
            if attempt < max_retries:
                time.sleep(5)
            else:
                webhooks.error("Failed to upload short after {} attempts: {}".format(max_retries + 1, e))
                raise

def create_vod():
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            clip_downloader = clip_download.ClipsDownloader()
            selected_vod = vod_fetch.get_relevant_vod()

            clips, vod_title = vod_fetch.get_vod_clips(str(selected_vod))
            directory = f'content/output/{sanitize_path(vod_title)}'

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

            vod.generate_video(f'content/output/{sanitize_path(vod_title)}')
            video_id = youtube.upload_video(
                f'{directory}/product.mp4',
                top_clip['title'] + ' | ' + top_clip['broadcaster_name'] + ' Stream Highlights',
                top_clip['broadcaster_name'] + ' stream highlights\n\nSubscribe for more content like this!\n\nAll credits go to the original creator.\nFind them on Twitch @' + top_clip['broadcaster_name'] + '.',
                video_tags,
                '24',
                'private'
            )
            webhooks.success(f"Type: VOD Highlights\nTitle: {top_clip['title'] + ' | ' + top_clip['broadcaster_name'] + ' Stream Highlights'}\nVideo link: https://www.youtube.com/watch?v={video_id}")
            if os.path.exists(directory):
                shutil.rmtree(directory)
            break

        except Exception as e:
            if attempt < max_retries:
                time.sleep(5)
            else:
                webhooks.error("Failed to upload VOD highlight after {} attempts: {}".format(max_retries + 1, e))
                raise

def create_highlights():
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            clip_downloader = clip_download.ClipsDownloader()
            clips = clip_fetch.fetch_streamer_highlights()
            
            top_clip = clips[next(iter(clips))]
            directory = f'content/output/{sanitize_path(top_clip["url"].split("-")[-1])}'
            
            clip_order = 0
            for _, data in clips.items():
                clip_order += 1
                clip_downloader.download_clip(
                    data,
                    "vod",
                    top_clip["url"].split('-')[-1],
                    str(clip_order)
                )
                time.sleep(1)
            
            vod.generate_video(directory)
            video_id = youtube.upload_video(
                directory + "/product.mp4",
                top_clip['title'] + ' | Best of ' + top_clip['broadcaster_name'],
                'Best of ' + top_clip['broadcaster_name'] + '.\n\nSubscribe for more content like this!\n\nAll credits go to the original creator.\nFind them on Twitch @' + top_clip['broadcaster_name'] + '.',
                video_tags,
                '24',
                'private'
            )
            
            webhooks.success(f"Type: Streamer Highlights\nTitle: {top_clip['title'] + ' | Best of ' + top_clip['broadcaster_name']}\nVideo link: https://www.youtube.com/watch?v={video_id}")
            if os.path.exists(directory):
                shutil.rmtree(directory)
            break 

        except Exception as e:
            if attempt < max_retries:
                time.sleep(5)
            else:
                webhooks.error(f"Failed to create highlights after {max_retries + 1} attempts: {e}")
                raise

def select_video():
    options = [create_vod, create_highlights]
    choice = random.choice(options)
    choice()
'''
schedule.every().day.at("17:30").do(select_video)
schedule.every().day.at("14:30").do(create_short)

while True:
    schedule.run_pending()
    time.sleep(300)
'''

create_vod()