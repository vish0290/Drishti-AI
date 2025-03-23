from google import genai
from google.genai import types 
from dotenv import load_dotenv
import os, re
import base64
from PIL import Image
import io
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
sys_instruct="you are an AI assistant whose main task is to help people with notifying what is in the image based on the user query. give the output in single paragraph."
g_client = genai.Client(api_key=api_key)

def get_image_type(base64_string):
    match = re.match(r'data:image/(?P<type>\w+);base64,', base64_string)
    if match:
        return match.group('type')
    return None

def resize_image(image_data, target_size=(512, 512)):
    try:
        # Open the image with PIL
        img = Image.open(io.BytesIO(image_data))
        
        # Get original image format
        img_format = img.format or "JPEG"
        
        # Calculate new dimensions (maintaining aspect ratio)
        original_width, original_height = img.size
        ratio = min(target_size[0] / original_width, target_size[1] / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Resize the image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=img_format)
        resized_data = output_buffer.getvalue()
        
        # Determine mime type
        mime_type = f"image/{img_format.lower()}"
        
        return resized_data, mime_type
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        # Return original data if resize fails
        return image_data, None

def google_client(img_base64: str, query: str, target_size=(512, 512)):
    try:
        # Check if the base64 string includes the data URL prefix
        if ',' in img_base64:
            # Split off the data URL prefix if present
            img_base64 = img_base64.split(',', 1)[1]
        
        # Decode the base64 image
        image_data = base64.b64decode(img_base64)
        
        # Get original image type
        image_type = get_image_type(img_base64) or "jpeg"
        
        # Resize the image
        resized_image, mime_type = resize_image(image_data, target_size)
        
        # Use determined mime type or fall back to original
        if not mime_type:
            mime_type = f"image/{image_type}"
        
        # Call Gemini API with resized image
        response = g_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct
            ),
            contents=[
                query,
                types.Part.from_bytes(data=resized_image, mime_type=mime_type)
            ]
        )
        
        return response.text
    except Exception as e:
        print(f"Error in google_client: {str(e)}")
        return f"Sorry, I couldn't process that image. Error: {str(e)}"

