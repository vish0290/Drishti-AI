from fastapi import FastAPI,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from utils.auth_manager import UserManager
from utils.speech_recognition import stt
from utils.text_2_speech import tts
from utils.core import google_client
from typing import Optional
import os,shutil


app = FastAPI()

# CORS middleware setup remains the same
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_input: str
    img_base64: str

class TranscribeRequest(BaseModel):
    audio: str
    format: str = "wav"

class user(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    
def delete_audio_files():
     # Your cleanup function remains unchanged
     audio_folder = "./audio"
     for filename in os.listdir(audio_folder):
         file_path = os.path.join(audio_folder, filename)
         try:
             if os.path.isfile(file_path) or os.path.islink(file_path):
                 os.unlink(file_path)
             elif os.path.isdir(file_path):
                 shutil.rmtree(file_path)
         except Exception as e:
             print(f'Failed to delete {file_path}. Reason: {e}')

@app.get("/")
def health():
    return {"status": "ok"}

@app.post('/register')
def register(request:user):
    auth_manager = UserManager()
    response = auth_manager.add_user(request.username, request.email, request.password)
    if response['success']:
        return JSONResponse(status_code=200, content={"message": response['message'], "api_key": response['api_key']})
    else:
        return JSONResponse(status_code=500, content={"message": response['message']})

@app.post('/login')
def login(request:user):
    auth_manager = UserManager()
    response = auth_manager.authenticate_user(request.username, request.password)
    if response['success']:
        return JSONResponse(status_code=200, content={"message": response['message'], "api_key": response['api_key']})
    else:
        return JSONResponse(status_code=500, content={"message": response['message']})


@app.post('/transcribe')
async def transcribe(request: TranscribeRequest,authorization : Optional[str] = None):
    print("Received transcription request")
    
    if not authorization:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    auth_manager = UserManager()
    if not auth_manager.check_api_key(authorization):
        return JSONResponse(status_code=401, content={"message": "Invalid API key"})
    data = stt(request.audio, request.format)
    if data['flag']:
        return JSONResponse(status_code=200, content={"text": data['text']})
    else:
        return JSONResponse(status_code=500, content={"message": data['text']})


@app.post('/query')
def resp(request: QueryRequest,background_tasks:BackgroundTasks, authorization : Optional[str] = None,):
    if not authorization:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    auth_manager = UserManager()
    if not auth_manager.check_api_key(authorization):
        return JSONResponse(status_code=401, content={"message": "Invalid API key"})   
    if not request.user_input:
        return JSONResponse(status_code=400, content={"message": "Query is required"})
    if not request.img_base64:
        return JSONResponse(status_code=400, content={"message": "Image is required"})
    else:
        text_response = google_client(request.img_base64, request.user_input)
        res = tts(text_response)
        if res['flag']:
            background_tasks.add_task(delete_audio_files)
            return FileResponse(f'audio/{res["id"]}.wav', media_type='audio/wav', filename=f'response.wav')
        else:
            return JSONResponse(status_code=500, content={"message": "Failed to generate audio"})
        

