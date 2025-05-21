from fastapi import FastAPI, Request, responses
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from pytubefix import YouTube
from dotenv import load_dotenv
import subprocess
import asyncio
import uuid
import os
import re
import gc

# --- Configurações iniciais ---
app = FastAPI()

load_dotenv()
BASE_URL = os.getenv("BASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
DOWNLOAD_DIR = "downloads"
FINAL_DIR = "final"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

downloads_temp = {}

# Resoluções permitidas
ALLOWED_RESOLUTIONS = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]

# --- Funções Auxiliares ---

def get_itags(yt, itag=None):
    available_streams = []
    for s in yt.streams:
        is_audio = s.includes_audio_track and not s.resolution
        stream_type = s.abr if is_audio else (s.resolution or "unknown")
        if stream_type in ALLOWED_RESOLUTIONS:
            available_streams.append({
                "itag": s.itag,
                "type": "áudio" if is_audio else "vídeo",
                "resolution": stream_type,
                "mime_type": s.mime_type,
            })

    if itag:
        return {
            "error": f"Nenhum stream encontrado com itag {itag}",
            "disponíveis": available_streams,
        }
    return {"disponíveis": available_streams}

async def delete_after_timeout(file_id: str, timeout: int = 60):
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

def convert_to_mp3(input_path, output_path):
    command = ['ffmpeg', '-y', '-i', input_path, output_path]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- Rotas da API ---

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/get_itag")
async def get_itags_route(request: Request):
    data = await request.json()
    url = data.get('url')
    itag = data.get('itag')

    if not url:
        return {"error": "URL não fornecida"}

    try:
        yt = YouTube(url, 'WEB')
        result = get_itags(yt, itag)
        del yt
        gc.collect()
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/info")
async def get_video_info(request: Request):
    data = await request.json()
    url = data.get('url')

    if not url or not isinstance(url, str):
        return {"error": "URL inválida"}

    try:
        yt = YouTube(url, 'WEB')
        info = responses.JSONResponse(content={
            'title': yt.title,
            'author': yt.author,
            'length': yt.length,
            'views': yt.views,
            'thumbnail_url': yt.thumbnail_url,
            'url': yt.watch_url,
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
            ],
        })
        del yt
        gc.collect()
        return info
    except Exception as e:
        return {"error": str(e)}

@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get('url')
    itag = data.get('itag')

    if not url:
        return {"error": "URL não fornecida"}
    if not itag:
        return {"error": "itag não fornecido"}

    try:
        yt = YouTube(url, 'WEB')
        stream = yt.streams.get_by_itag(itag)
        title = sanitize_filename(yt.title)

        is_audio = stream.mime_type.startswith("audio/")
        resolution = "audio" if is_audio else (stream.resolution or "unknown")

        if resolution not in ALLOWED_RESOLUTIONS and resolution != "1080p":
            del yt
            del stream
            gc.collect()
            return {"error": f"Resolução {resolution} não permitida. Apenas {', '.join(ALLOWED_RESOLUTIONS)} e 1080p são permitidas."}

        if is_audio:
            ext = ".webm" if "webm" in stream.mime_type else ".m4a"
            raw_filename = f"{title}_{stream.abr}{ext}"
            raw_path = os.path.join(DOWNLOAD_DIR, raw_filename)
            stream.download(output_path=DOWNLOAD_DIR, filename=raw_filename)

            mp3_filename = f"{title}_{stream.abr}.mp3"
            mp3_path = os.path.join(DOWNLOAD_DIR, mp3_filename)
            convert_to_mp3(raw_path, mp3_path)
            os.remove(raw_path)

            final_path = os.path.join(FINAL_DIR, os.path.basename(mp3_path))
            os.rename(mp3_path, final_path)

            file_id = str(uuid.uuid4())
            downloads_temp[file_id] = {"path": final_path}
            asyncio.create_task(delete_after_timeout(file_id))

            del yt
            del stream
            gc.collect()

            return {"message": "Áudio convertido para MP3", "download_url": f"{BASE_URL}/download/{file_id}"}

        elif not stream.includes_audio_track:
            video_path = os.path.join(DOWNLOAD_DIR, f"{title}_{resolution}_video.mp4")
            stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(video_path))

            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            audio_ext = ".webm" if "webm" in audio_stream.mime_type else ".m4a"
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
            asyncio.create_task(delete_after_timeout(file_id))

            del yt
            del stream
            del audio_stream
            gc.collect()

            return {"message": f"Vídeo {resolution} com áudio mesclado", "download_url": f"{BASE_URL}/download/{file_id}"}

        else:
            filename = f"{title}_{resolution}.mp4"
            download_path = os.path.join(DOWNLOAD_DIR, filename)
            stream.download(output_path=DOWNLOAD_DIR, filename=filename)

            file_id = str(uuid.uuid4())
            downloads_temp[file_id] = {"path": download_path}
            asyncio.create_task(delete_after_timeout(file_id))

            del yt
            del stream
            gc.collect()

            return {"message": f"Vídeo {resolution} com áudio embutido", "download_url": f"{BASE_URL}/download/{file_id}"}

    except Exception as e:
        return {"error": str(e)}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    file_info = downloads_temp.pop(file_id, None)
    if not file_info:
        return {"error": "Arquivo expirado ou já baixado"}

    file_path = file_info["path"]
    if not os.path.exists(file_path):
        return {"error": "Arquivo não encontrado"}

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream',
        background=BackgroundTask(lambda: os.remove(file_path)),
    )