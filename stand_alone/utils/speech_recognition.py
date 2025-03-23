from faster_whisper import WhisperModel
import tempfile
import base64

model_size = "distil-large-v3"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


def decode_base64_to_temp(base64_audio: str, audio_format) -> str:
    audio_data = base64.b64decode(base64_audio)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as f:
        f.write(audio_data)
        return f.name

def stt(base64_audio: str, audio_type: str) -> str:
    try:
        audio_path = decode_base64_to_temp(base64_audio, audio_type)
        segments, _ = model.transcribe(audio_path, beam_size=5)
        transcription = "".join([segment.text for segment in segments])
        return {"text": transcription, "flag": True}
    except Exception as e:
        return {"text": "Failed to process audio", "flag": False}
    
