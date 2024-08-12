import time
import modules.twitch.clip_fetch as clip_fetch
import modules.video.shorts as shorts
import modules.youtube.youtube as youtube

def create_short():
    max_retries = 3
    retry_delay = 2

    json_file_path = 'modules/util/video_tags.json'
    tags = youtube.load_tags(json_file_path)

    for attempt in range(max_retries):
        try:
            clip = clip_fetch.retrieve_clip()        
            shorts.generate_video(clip)
            youtube.upload_video(
                f'content/shorts/{clip.title.replace(" ", "_").replace("/", "_").lower()}/product.mp4',
                clip.title + " #shorts #clips",
                "Featured streamer: " + clip.broadcaster_name + "\n\nSubscribe for more content like this!",
                tags,
                '24'
            )
            break
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print("Operation failed.")

