from kokoro import KPipeline
import soundfile as sf
import torch
from uuid import uuid4
pipeline = KPipeline(lang_code='a')

from io import BytesIO
import base64

base64_audio_list = []
def tts(text,voice='af_heart',speed=1):
    pipeline = KPipeline(lang_code='a') 
    generator = pipeline(
         text, voice=voice,
         speed=speed
     )
    id = uuid4()
    for i, (gs, ps, audio) in enumerate(generator):
        sf.write(f'audio/{id}.wav', audio, 24000)
        return {'flag':True,'id':id}
    return {'flag':False}
