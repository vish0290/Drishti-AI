import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from openai import OpenAI
from kokoro import KPipeline
import soundfile as sf
from pydantic import BaseModel
import requests
load_dotenv()

class resp(BaseModel):
    msg: str

moon_dream_key = os.getenv("MOON_DREAM_KEY")
img_client = OpenAI(base_url="https://api.moondream.ai/v1", api_key=moon_dream_key)
agent = Agent(model='groq:llama-3.1-8b-instant',system_prompt='you are an AI assistant whose main task is to help people with notifying what is in the image you are given with image details and user query',result_type=resp)


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
        'Content-Type': 'application/json',
        'X-Moondream-Auth': moon_dream_key
    }
    json_data = {
        'image_url': img_base64,
        'length': 'normal',
        'stream': False,
    }
    response = requests.post('https://api.moondream.ai/v1/caption', headers=headers, json=json_data).json()
    return response.get('caption')


def query_data(user_input:str, img_base64:str) -> str:
    img_data = image_data(img_base64)
    res = agent.run_sync(f'here is the image data: {img_data} and the user query is: {user_input}')
    final_res = tts_gen(res.data.msg)
    return final_res