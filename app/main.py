from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from starlette.background import BackgroundTask
from pytubefix import YouTube
from dotenv import load_dotenv

from app.utils import get_video_resolutions, get_video_info, delete_after_timeout, sanitize_filename

import subprocess
import asyncio
import uuid
import os
import re
import gc

# --- Default settings ---
app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

#  --- permissions ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- .env ---
load_dotenv()

URL_BASE = os.getenv("URL_BASE")

# *SECURiTY* verify if you it has the necessary directories
DOWNLOAD_DIR = "downloads"
FINAL_DIR = "final"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

os.makedirs(FINAL_DIR, exist_ok=True)


# --- Global variables ---
downloads_temp = {}

ALLOWED_RESOLUTIONS = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]

clients = ["WEB","WEB_EMBED","WEB_MUSIC","WEB_CREATOR","WEB_SAFARI","MWEB","WEB_KIDS","ANDROID","ANDROID_VR","ANDROID_MUSIC","ANDROID_CREATOR","ANDROID_TESTSUITE","ANDROID_PRODUCER","ANDROID_KIDS","IOS","IOS_MUSIC","IOS_CREATOR","IOS_KIDS"]

# --- Rotas da API ---

@app.get("/", response_class=HTMLResponse)
def serve_index():
    html_path = os.path.join("assets", "index.html")
    with open(html_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/config")
def config_route():
    return {
        "version": "1.0.0",
        "author": "Vinicius Dizatnikis",
        "lib":  "pytubefix",
        "token_method": {
            "using_token": "Using the token method with a client may sometimes result in an unsuccessful request, depending on pytubefix",
            "not_using_token": "Not using the token method will result in a successful request, but your IP might be blocked by YouTube",
            "clients": [
                "WEB",
                "WEB_EMBED",
                "WEB_MUSIC",
                "WEB_CREATOR",
                "WEB_SAFARI",
                "MWEB",
                "WEB_KIDS",
                "ANDROID",
                "ANDROID_VR",
                "ANDROID_MUSIC",
                "ANDROID_CREATOR",
                "ANDROID_TESTSUITE",
                "ANDROID_PRODUCER",
                "ANDROID_KIDS",
                "IOS",
                "IOS_MUSIC",
                "IOS_CREATOR",
                "IOS_KIDS"
            ]
        }
    }


@app.post("/resolutions")
async def resolutions_route(request: Request):

    data = await request.json()

    url = data.get('url')

    token_method = data.get('token_method')

    if token_method:
        token_method = token_method.upper()
    else:
        token_method = None

    used_token_method = False

    if not url:
        return {
            "Attention": "URL not found"
            }

    try:
        if token_method in clients:
            yt = YouTube(url, token_method)
            used_token_method = True
        else:
            yt = YouTube(url)
                

        result = get_video_resolutions(yt)

        if used_token_method:
            return {
                "status": "success",
                "token_method": used_token_method,
                "client_of_token": token_method,
                "Result": result
                }
        else:
            return {
                "status": "success",
                "token_method": used_token_method,
                "Result": result
                } 
    except Exception as e:
         return {
            "status": "error",
            "error": str(e)
            }
    finally:
        if yt:
            del yt
            gc.collect()
    

@app.post("/info")
async def info_route(request: Request):  

    data = await request.json()

    url = data.get('url')

    token_method = data.get('token_method')

    if token_method:
        token_method = token_method.upper()
    else:
        token_method = None
    
    used_token_method = False
    
    if not url:
        return {
            "status": "error",
            "Attention": "URL not found"
            }

    try:
        if token_method in clients:
            yt = YouTube(url, token_method)
            used_token_method = True
        else:
            yt = YouTube(url)

        result = get_video_info(yt)  

        if used_token_method:
            return {
                "status": "success",
                "token_method": used_token_method,
                "client_of_token": token_method,
                "Result": result
                }
        else:
            return {
                "status": "success",
                "token_method": used_token_method,
                "Result": result
                }                
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
            }
    finally:
        if yt:
            del yt
            gc.collect()

    

@app.post("/download")
async def download_route(request: Request):
    data = await request.json()

    url = data.get('url')

    itag = data.get('itag')

    token_method = data.get('token_method')

    if token_method:
        token_method = token_method.upper()
    else:
        token_method = None

    used_token_method = False


    if not url:
        return {
            "Attention": "URL not found"
            }
    if not itag:
        return {
            "Attention": "itag not found"
            }
    

    try:
        if token_method in clients:
            yt = YouTube(url, token_method)
            used_token_method = True
        else:
            yt = YouTube(url)

        stream = yt.streams.get_by_itag(itag)

        title = sanitize_filename(yt.title)

        is_audio = stream.mime_type.startswith("audio/")

        resolution = "audio" if is_audio else (stream.resolution or "unknown")

        if resolution not in ALLOWED_RESOLUTIONS:
            return {
                "status": "error",
                "error": f"Resolution {resolution} not allowed. Just {', '.join(ALLOWED_RESOLUTIONS)} are alowed."
                }

        if is_audio:
            type_audio = None

            if stream.mime_type == "audio/webm":
                type_audio = ".webm"
            elif stream.mime_type == "audio/mp4":
                type_audio = ".mp4"

            try:
                raw_filename = f"{title}_{stream.abr}{type_audio}"

                final_path = stream.download(output_path=FINAL_DIR, filename=raw_filename)

                file_id = str(uuid.uuid4())

                downloads_temp[file_id] = {"path": final_path}

                asyncio.create_task(delete_after_timeout(file_id, downloads_temp))

                result = {
                "message": "Audio success downloaded", 
                "url_download": f"{URL_BASE}/download/{file_id}"
                }
                
                if used_token_method:
                    return {
                    "status": "success",
                    "token_method": used_token_method,
                    "client_of_token": token_method,
                    "Result": result
                    }
                else:
                    return {
                    "status": "success",
                    "token_method": used_token_method,
                    "Result": result
                }                  
            except Exception as e:
                 return {
                "status": "error",
                "error": str(e)
                }
            finally:
                if yt:
                    del yt
                if stream:
                    del stream

                gc.collect()


        elif not stream.includes_audio_track:
            try:
                video_path = os.path.join(DOWNLOAD_DIR, f"{title}_{resolution}_video.mp4")

                stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(video_path))

                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

                audio_ext = ".webm" if "webm" in audio_stream.mime_type else ".mp4"

                audio_path = os.path.join(DOWNLOAD_DIR, f"{title}_audio{audio_ext}")

                audio_stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(audio_path))

                final_path = os.path.join(FINAL_DIR, f"{title}_{resolution}.mp4")

                command = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-strict", "experimental",
                    final_path,
                ]

                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                os.remove(video_path)
                os.remove(audio_path)

                file_id = str(uuid.uuid4())

                downloads_temp[file_id] = {"path": final_path}

                asyncio.create_task(delete_after_timeout(file_id, downloads_temp))

                return {
                    "status": "success",
                    "token_method": used_token_method,
                    "message": f"Video {title} with mixed audio", 
                    "url_download": f"{URL_BASE}/download/{file_id}"
                    }
            except Exception as e:
                 return {
                "status": "error",
                "error": str(e)
                }
            finally:
                if yt:
                    del yt
                if stream:
                    del stream
                if audio_stream:
                    del audio_stream
                gc.collect()

        else:
            try:
                filename = f"{title}_{resolution}.mp4"

                download_path = os.path.join(DOWNLOAD_DIR, filename)

                stream.download(output_path=DOWNLOAD_DIR, filename=filename)

                file_id = str(uuid.uuid4())

                downloads_temp[file_id] = {"path": download_path}

                asyncio.create_task(delete_after_timeout(file_id, downloads_temp))

                return {
                    "message": f"Vídeo {resolution} com áudio embutido", 
                    "url_download": f"{URL_BASE}/download/{file_id}"
                    }
            except Exception as e:
                 return {
                "status": "error",
                "error": str(e)
                }
            finally:
                if yt:
                    del yt
                if stream:
                    del stream
                gc.collect()

    except Exception as e:
         return {
            "status": "error",
            "error": str(e)
            }
    

@app.get("/download/{file_id}")
async def download_file_route(file_id: str):

    file_info = downloads_temp.pop(file_id)

    if not file_info:
        return {
            "status": "error",
            "error": "archive not found"
            }

    file_path = file_info["path"]

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error": "archive not found"
            }

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream',
        background=BackgroundTask(lambda: os.remove(file_path)),
    )