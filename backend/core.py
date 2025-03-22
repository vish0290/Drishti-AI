import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from openai import OpenAI
from kokoro import KPipeline
import soundfile as sf
from pydantic import BaseModel
from openai import OpenAI
import httpx
import re
import requests
import base64
import uuid
from faster_whisper import WhisperModel
from google import genai
from google.genai import types 
load_dotenv()

class resp(BaseModel):
    msg: str

moon_dream_key = os.getenv("MOON_DREAM_KEY")
img_client = OpenAI(api_key=os.getenv("MOON_DREAM_KEY"))
agent = Agent(model='groq:llama-3.2-3b-preview',system_prompt='you are an AI assistant whose main task is to help people with notifying what is in the image based on the user query. give the output in single paragraph.')
model_size = "large-v3"
sr_model = WhisperModel(model_size, device="cpu", compute_type="int8")


api_key = os.getenv("GEMINI_API_KEY")
sys_instruct="you are an AI assistant whose main task is to help people with notifying what is in the image based on the user query. give the output in single paragraph."
g_client = genai.Client(api_key=api_key)

# for gpu  
# sr_model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")


def get_image_type(base64_string):
    match = re.match(r'data:image/(?P<type>\w+);base64,', base64_string)
    if match:
        return match.group('type')
    return None

# Example usage
base64_data = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA2ADYAAD/7QA4UGhvdG9zaG9wIDMuMAA4Qkl"
image_type = get_image_type(base64_data)
print("Image Type:", image_type)

def speech_to_text(audio:str,file_type:str) -> str:
    #convert base64 audio to wav file
    try:
        audio_data = base64.b64decode(audio)
        audio_id = str(uuid.uuid4())
        audio_path = f'./input_audio/{audio_id}.{file_type}'
        with open(audio_path, 'wb') as f:
            f.write(audio_data)
    except Exception as e:
        return {'text': "Failed to process audio", 'flag':False}
    
    #read the wav file to get the text
    try:
        segments, info = sr_model.transcribe(audio_path, beam_size=5) 
        for segment in segments:
            return {"text": segment.text,'flag':True}
    except Exception as e:
        return {'text': "Failed to process audio", 'flag':False}
    
def tts_gen(query, voice='af_heart', speed=1):
    pipeline = KPipeline(lang_code='a') 
    generator = pipeline(
        query, voice=voice,
        speed=speed
    )
    for i, (gs, ps, audio) in enumerate(generator):
        sf.write(f'audio/{i}.wav', audio, 24000)
        return True
    return False


def image_data(img_base64:str) -> str:
    headers = {
    'X-Moondream-Auth': moon_dream_key,
    'Content-Type': 'application/json',
    }
    json_data = {
    'image_url': img_base64,
    'length': 'normal',
    'stream': False,
    } 
    response = requests.post('https://api.moondream.ai/v1/caption', headers=headers, json=json_data).json()
    return response.get('caption')


def google_client(img_base64:str,query:str):
    image = base64.b64decode(img_base64)
    image_type = get_image_type(img_base64)
    response = g_client.models.generate_content(
        model="gemini-2.0-flash-exp",
        config=types.GenerateContentConfig(
        system_instruction=sys_instruct),
        contents=[query,
                types.Part.from_bytes(data=image, mime_type=f"image/{image_type}")]
    )
    return response.text

def query_data(user_input:str, img_base64:str) -> str:
    # img_data = image_data(img_base64)
    # res = agent.run_sync(f'here is the image data: {img_data} and the user query is: {user_input} generate the answer based on the query')
    # final_res = tts_gen(res.data)
    
    # res = groq_client(img_base64, user_input)
    res = google_client(img_base64, user_input)
    final_res = tts_gen(res)
    return final_res


