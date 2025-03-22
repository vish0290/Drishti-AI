import os
import shutil
import base64
import uuid
import io
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from core import query_data, speech_to_text


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

# The rest of your initial setup code remains unchanged
INPUT_AUDIO_DIR = "./input_audio"
os.makedirs(INPUT_AUDIO_DIR, exist_ok=True)

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

@app.post('/transcribe')
async def transcribe(request: TranscribeRequest):
    print("Received transcription request")
    data = speech_to_text(request.audio, request.format)
    if data['flag']:
        return JSONResponse(status_code=200, content={"text": data['text']})
    else:
        return JSONResponse(status_code=500, content={"message": data['text']})


@app.post('/query')
def resp(request: QueryRequest, background_tasks: BackgroundTasks):
    if not request.user_input:
        return JSONResponse(status_code=400, content={"message": "Query is required"})
    if not request.img_base64:
        return JSONResponse(status_code=400, content={"message": "Image is required"})
    else:
        resp = query_data(request.user_input, request.img_base64)
        if resp:
            background_tasks.add_task(delete_audio_files)
            return FileResponse("./audio/0.wav", media_type='audio/wav', filename="output.wav")
        else:
            return JSONResponse(status_code=500, content={"message": "Failed"})

@app.post('/demo_audio')
def demo_base64(request:TranscribeRequest):
    audio_data = base64.b64decode(request.audio)
    with open("write.wav", "wb") as f:
        f.write(audio_data)
    return {"message": "Audio saved as demo.wav"}