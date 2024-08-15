import os
import random
import numpy as np
from modules.util.sanitization import sanitize_path
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from PIL import Image, ImageFilter

def blur_frame(frame, blur_radius):
    img = Image.fromarray(frame)
    blurred_img = img.filter(ImageFilter.GaussianBlur(blur_radius))
    return np.array(blurred_img)

def generate_video(clip):
    video = VideoFileClip(f'content/output/{sanitize_path(clip.title)}' + "/raw_clip.mp4")#.subclip(0, 1)

    # Formatting
    shorts_width = 720
    shorts_height = 1280

    original_width, original_height = video.size
    original_aspect_ratio = original_width / original_height

    if shorts_width / shorts_height > original_aspect_ratio:
        new_height = shorts_height
        new_width = int(new_height * original_aspect_ratio)
    else:
        new_width = shorts_width
        new_height = int(new_width / original_aspect_ratio)

    resized_video = video.resize(newsize=(new_width, new_height))
    blurred_video = video.fx(lambda clip: clip.fl_image(lambda frame: blur_frame(frame, 20)))
    section_height = shorts_height // 2

    top_blurred = blurred_video.crop(x1=0, x2=shorts_width, y1=0, y2=section_height)
    bottom_blurred = blurred_video.crop(x1=0, x2=shorts_width, y1=new_height - section_height, y2=new_height)

    offset = section_height // 2

    top_blurred = blurred_video.crop(x1=0, x2=shorts_width, y1=0, y2=section_height)
    bottom_blurred = blurred_video.crop(x1=0, x2=shorts_width, y1=section_height - offset, y2=section_height + new_height - offset)

    top_blurred = top_blurred.set_position(('center', 'top')).set_duration(video.duration)
    bottom_blurred = bottom_blurred.set_position(('center', 'bottom')).set_duration(video.duration)

    zoom_factor = 1.2
    zoomed_center_video = resized_video.resize(newsize=(int(new_width * zoom_factor), int(new_height * zoom_factor)))
    centered_video = zoomed_center_video.set_position(('center', 'center'))

    # Text
    center_video_y = shorts_height // 2
    padding = 40
    available_height = center_video_y - padding
    custom_font_path = "fonts/helvetica-compressed-5871d14b6903a.otf"

    def get_text_clip(text, width, height, fontsize=60, stroke_width=3.5, color='white'):
        stroke_color = 'black'
        shadow_offset = (5, 5)
        
        while True:
            shadow_clip = TextClip(
                text,
                color='black',
                font=custom_font_path,
                fontsize=fontsize,
                size=(width, height),
                method='caption',
                stroke_color=None,
                stroke_width=0
            ).set_position((shadow_offset[0], shadow_offset[1]))

            txt_clip = TextClip(
                text,
                color=color,
                font=custom_font_path,
                fontsize=fontsize,
                size=(width, height),
                method='caption',
                stroke_color=stroke_color,
                stroke_width=stroke_width
            )

            shadow_txt_clip = CompositeVideoClip([shadow_clip, txt_clip])
            
            if txt_clip.h <= height:
                break
            fontsize -= 2
        
        return shadow_txt_clip

    colors = ["#ff00f7", "#00fffd", "#09ff00", "#fffb01"]
    random_color = random.choice(colors)

    text = clip.title.upper()
    txt_clip = get_text_clip(text, shorts_width - 2 * padding, available_height, fontsize=70, stroke_width=2, color=random_color)

    if len(text) <= 25:
        manual_adjustment = 10
    else:
        manual_adjustment = -80

    text_vertical_position = center_video_y - (available_height // 2) - txt_clip.h / 2 + manual_adjustment
    txt_clip = txt_clip.set_pos(('center', text_vertical_position)).set_duration(video.duration)

    bottom_text = "twitch.tv/" + clip.broadcaster_name
    bottom_fontsize = 30
    bottom_stroke_width = 1
    bottom_txt_clip = get_text_clip(bottom_text, shorts_width - 2 * padding, shorts_height // 4, fontsize=bottom_fontsize, stroke_width=bottom_stroke_width, color="white")
    
    bottom_text_vertical_position = shorts_height - shorts_height // 4 - 215
    bottom_txt_clip = bottom_txt_clip.set_pos(('center', bottom_text_vertical_position)).set_duration(video.duration)

    # Combine clips
    final_video = CompositeVideoClip([top_blurred, bottom_blurred, centered_video, txt_clip, bottom_txt_clip], size=(shorts_width, shorts_height))
    final_video = final_video.set_duration(video.duration)

    output_path = os.path.join(f'content/output/{sanitize_path(clip.title)}', "product" + ".mp4")
    final_video.write_videofile(output_path, codec="libx264")