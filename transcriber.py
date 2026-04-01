# transcriber.py
# Yeh file audio file leti hai aur Whisper se text mein convert karti hai.
# Whisper OpenAI ka open source model hai — bilkul free, locally run hota hai.

import whisper
import os

# Global variable — model ek baar load hoga, baar baar nahi
# Yeh important hai kyunke model load karne mein 10-15 second lagte hain
_model = None

def get_model():
    """
    Whisper model lazy load karo — sirf jab pehli baar zaroorat ho.
    'base' model use kar rahe hain kyunke:
    - Free deployment (HuggingFace) ke liye kaafi accurate hai (~95% English)
    - Download size sirf ~140MB hai
    - 'small' se 3x faster hai
    """
    global _model
    if _model is None:
        print("Loading Whisper model... (sirf pehli baar hoga)")
        _model = whisper.load_model("base")
        print("Whisper model ready!")
    return _model


def transcribe_audio(audio_path: str) -> dict:
    """
    Audio file ka path lo aur transcription return karo.
    
    Returns:
        dict with keys:
        - success: bool
        - text: full transcript string
        - language: detected language
        - error: error message if failed
    """
    if not audio_path:
        return {"success": False, "error": "No audio file provided."}
    
    # File exist karta hai?
    if not os.path.exists(audio_path):
        return {"success": False, "error": f"File not found: {audio_path}"}
    
    # File size check — 25MB limit rakho
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > 25:
        return {
            "success": False, 
            "error": f"File too large ({file_size_mb:.1f}MB). Please use a file under 25MB."
        }
    
    try:
        model = get_model()
        
        print(f"Transcribing: {audio_path} ({file_size_mb:.1f}MB)")
        
        # Whisper transcribe — fp16=False CPU ke liye zaroori hai
        result = model.transcribe(
            audio_path,
            fp16=False,        # CPU par float32 use karo
            verbose=False,     # Console mein progress mat dikhao
        )
        
        transcript = result["text"].strip()
        language   = result.get("language", "unknown")
        
        if not transcript:
            return {"success": False, "error": "No speech detected in the audio."}
        
        return {
            "success":  True,
            "text":     transcript,
            "language": language,
        }
    
    except Exception as e:
        return {"success": False, "error": f"Transcription failed: {str(e)}"}