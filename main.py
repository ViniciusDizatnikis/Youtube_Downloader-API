from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
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

# --- Inicialização ---
app = FastAPI()
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
FINAL_DIR = "final"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

downloads_temp = {}
ALLOWED_RESOLUTIONS = ["1080p", "720p", "480p", "360p", "240p", "144p", "audio"]

# --- Funções Auxiliares ---

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

async def delete_after_timeout(file_id: str, timeout: int = 60):
    await asyncio.sleep(timeout)
    file_info = downloads_temp.pop(file_id, None)
    if file_info and os.path.exists(file_info["path"]):
        os.remove(file_info["path"])
    gc.collect()

def convert_to_mp3(input_path, output_path):
    subprocess.run(['ffmpeg', '-y', '-i', input_path, output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def download_with_ytdlp(url: str, output_path: str, audio_only: bool = False):
    template = os.path.join(output_path, '%(title)s.%(ext)s')
    command = ['yt-dlp', url, '-o', template]
    if audio_only:
        command += ['-f', 'bestaudio', '--extract-audio', '--audio-format', 'mp3']
    else:
        command += ['-f', 'bestvideo+bestaudio/best']
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return max([os.path.join(output_path, f) for f in os.listdir(output_path)], key=os.path.getmtime)

def get_itags(yt, itag=None):
    available = []
    for s in yt.streams:
        is_audio = s.includes_audio_track and not s.resolution
        res = s.abr if is_audio else (s.resolution or "unknown")
        if res in ALLOWED_RESOLUTIONS:
            available.append({
                "itag": s.itag,
                "type": "áudio" if is_audio else "vídeo",
                "resolution": res,
                "mime_type": s.mime_type,
            })
    return {"disponíveis": available} if not itag else {"error": f"itag {itag} não encontrada", "disponíveis": available}

# --- Rotas ---

@app.get("/")
def root():
    return {"message": "API de download de vídeos do YouTube"}

@app.post("/get_itag")
async def route_itags(request: Request):
    data = await request.json()
    try:
        yt = YouTube(data.get("url"), "ANDROID")
        return get_itags(yt, data.get("itag"))
    except Exception as e:
        return {"error": str(e)}

@app.post("/info")
async def route_info(request: Request):
    data = await request.json()
    try:
        yt = YouTube(data.get("url"), "ANDROID")
        return {
            'title': yt.title,
            'author': yt.author,
            'length': yt.length,
            'views': yt.views,
            'thumbnail_url': yt.thumbnail_url,
            'url': yt.watch_url,
            'video_streams': [
                {'itag': s.itag, 'resolution': s.resolution, 'mime_type': s.mime_type, 'includes_audio_track': s.includes_audio_track}
                for s in yt.streams.filter(type="video")
            ],
            'audio_streams': [
                {'itag': s.itag, 'abr': s.abr, 'mime_type': s.mime_type}
                for s in yt.streams.filter(only_audio=True)
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/download")
async def route_download(request: Request):
    data = await request.json()
    url = data.get("url")
    itag = data.get("itag")

    if not url or not itag:
        return {"error": "URL ou itag ausente"}

    try:
        yt = YouTube(url, "ANDROID")
        stream = yt.streams.get_by_itag(itag)
        if not stream:
            return {"error": f"itag {itag} inválida"}

        title = sanitize_filename(yt.title)
        is_audio = stream.mime_type.startswith("audio/")
        resolution = stream.abr if is_audio else (stream.resolution or "unknown")

        if resolution not in ALLOWED_RESOLUTIONS:
            return {"error": f"Resolução não suportada: {resolution}"}

        if is_audio:
            ext = ".webm" if "webm" in stream.mime_type else ".m4a"
            raw = os.path.join(DOWNLOAD_DIR, f"{title}_{resolution}{ext}")
            mp3 = os.path.join(FINAL_DIR, f"{title}_{resolution}.mp3")
            stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(raw))
            convert_to_mp3(raw, mp3)
            os.remove(raw)
            final_path = mp3
        elif not stream.includes_audio_track:
            video_path = os.path.join(DOWNLOAD_DIR, f"{title}_{resolution}_video.mp4")
            stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(video_path))
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            audio_ext = ".webm" if "webm" in audio_stream.mime_type else ".m4a"
            audio_path = os.path.join(DOWNLOAD_DIR, f"{title}_audio{audio_ext}")
            audio_stream.download(output_path=DOWNLOAD_DIR, filename=os.path.basename(audio_path))
            final_path = os.path.join(FINAL_DIR, f"{title}_{resolution}.mp4")
            subprocess.run([
                'ffmpeg', '-y', '-i', video_path, '-i', audio_path,
                '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
                final_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(video_path)
            os.remove(audio_path)
        else:
            filename = f"{title}_{resolution}.mp4"
            final_path = os.path.join(FINAL_DIR, filename)
            stream.download(output_path=FINAL_DIR, filename=filename)

        file_id = str(uuid.uuid4())
        downloads_temp[file_id] = {"path": final_path}
        asyncio.create_task(delete_after_timeout(file_id))
        return {"message": "Download pronto", "download_url": f"{BASE_URL}/download/{file_id}"}

    except Exception:
        try:
            is_audio = data.get('audio_only', False)
            final_path = download_with_ytdlp(url, FINAL_DIR, audio_only=is_audio)
            file_id = str(uuid.uuid4())
            downloads_temp[file_id] = {"path": final_path}
            asyncio.create_task(delete_after_timeout(file_id))
            return {"message": "Fallback com yt-dlp", "download_url": f"{BASE_URL}/download/{file_id}"}
        except Exception as fallback_error:
            return {"error": f"Erro total: {str(fallback_error)}"}

@app.get("/download/{file_id}")
async def route_file(file_id: str):
    file_info = downloads_temp.pop(file_id, None)
    if not file_info or not os.path.exists(file_info["path"]):
        return JSONResponse({"error": "Arquivo expirado ou não encontrado"})
    return FileResponse(
        path=file_info["path"],
        filename=os.path.basename(file_info["path"]),
        media_type='application/octet-stream',
        background=BackgroundTask(lambda: os.remove(file_info["path"]))
    )
