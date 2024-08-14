from moviepy.editor import VideoFileClip, concatenate_videoclips
import os

def generate_video(folder_path):
    video_files = sorted(
        [f for f in os.listdir(folder_path) if f.endswith('.mp4')],
        key=lambda x: int(os.path.splitext(x)[0])
    )

    clips = [VideoFileClip(os.path.join(folder_path, f)) for f in video_files]
    final_clip = concatenate_videoclips(clips)

    output_file = os.path.join(folder_path, 'product.mp4')

    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')

    final_clip.close()
    for clip in clips:
        clip.close()

    for video_file in video_files:
        os.remove(os.path.join(folder_path, video_file))