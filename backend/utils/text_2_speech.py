from kokoro import KPipeline
import soundfile as sf
import tempfile
import os
import io

pipeline = KPipeline(lang_code='a')

def text_to_speech(text: str, return_bytes: bool = False):
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()  # Close the file so it can be written to
        
        # Generate audio
        generator = pipeline(text, voice='af_heart', speed=1)
        sample_rate = 24000  # Default sample rate
        
        for i, (gs, ps, audio) in enumerate(generator):
            sf.write(temp_path, audio, sample_rate)
            
            if return_bytes:
                # Read the temp file as bytes
                with open(temp_path, 'rb') as f:
                    audio_bytes = f.read()
                
                # Clean up the temp file
                os.unlink(temp_path)
                
                return True, audio_bytes, sample_rate
            else:
                return True, temp_path, sample_rate
        
        # If generator doesn't yield anything (unlikely)
        if return_bytes:
            os.unlink(temp_path)
            return False, "Failed to generate audio", None
        else:
            return False, "Failed to generate audio", None
            
    except Exception as e:
        # Clean up in case of error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return False, str(e), None