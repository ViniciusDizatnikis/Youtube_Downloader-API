import asyncio
import os
import re
import gc

def get_video_resolutions(yt):

    resol =  {
        "Resolutions avalible for the video": {
                'video_streams': [
                    {
                        'itag': s.itag,
                        'resolution': s.resolution,
                        'mime_type': s.mime_type,
                        'includes_audio_track': s.includes_audio_track,
                    }
                    for s in yt.streams.filter(type="video")
                ],
                'audio_streams': [
                    {
                        'itag': s.itag,
                        'abr': s.abr,
                        'mime_type': s.mime_type,
                    }
                    for s in yt.streams.filter(only_audio=True)
                ]
                }
            }
    
    return resol

def get_video_info(yt):
    return {
        'title': yt.title,
        'author': yt.author,
        'length': yt.length,
        'views': yt.views,
        'thumbnail_url': yt.thumbnail_url,
        'url': yt.watch_url,
    }

async def delete_after_timeout(file_id: str, downloads_temp , timeout: int = 60):

    await asyncio.sleep(timeout)

    file_info = downloads_temp.pop(file_id, None)

    if file_info:
        try:
            if os.path.exists(file_info["path"]):
                os.remove(file_info["path"])
        except Exception:
            pass
    gc.collect()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)