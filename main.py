import modules.twitch.clip_fetch as clip_fetch

clips = clip_fetch.retrieve_vod_clips("")
print(clips)