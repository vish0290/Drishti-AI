from fastapi import FastAPI,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from backend.utils.auth_manager import AuthManager
from backend.utils.speech_recognition import stt
from backend.utils.text_2_speech import text_to_speech
from backend.utils.core import google_client
from typing import Optional



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

@app.get("/")
def health():
    return {"status": "ok"}

@app.post('/register')
def register(request:user):
    auth_manager = AuthManager()
    response = auth_manager.register_user(request.username, request.email, request.password)
    if response['success']:
        return JSONResponse(status_code=200, content={"message": response['message'], "api_key": response['api_key']})
    else:
        return JSONResponse(status_code=500, content={"message": response['message']})

@app.post('/login')
def login(request:user):
    auth_manager = AuthManager()
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
    auth_manager = AuthManager()
    if not auth_manager.is_valid_api_key(authorization):
        return JSONResponse(status_code=401, content={"message": "Invalid API key"})
    data = stt(request.audio, request.format)
    if data['flag']:
        return JSONResponse(status_code=200, content={"text": data['text']})
    else:
        return JSONResponse(status_code=500, content={"message": data['text']})


@app.post('/query')
def resp(request: QueryRequest,authorization : Optional[str] = None):
    if not authorization:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    auth_manager = AuthManager()
    if not auth_manager.is_valid_api_key(authorization):
        return JSONResponse(status_code=401, content={"message": "Invalid API key"})   
    if not request.user_input:
        return JSONResponse(status_code=400, content={"message": "Query is required"})
    if not request.img_base64:
        return JSONResponse(status_code=400, content={"message": "Image is required"})
    else:
        text_response = google_client(request.img_base64, request.user_input)
        success, result, sample_rate = text_to_speech(text_response)
        if not success:
            return JSONResponse(status_code=500, content={"message": result})
        return Response(content=result, media_type="audio/wav", headers={"Content-Disposition": "attachment; filename=response.wav"})  
