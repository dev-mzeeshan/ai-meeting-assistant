# analyzer.py
# Transcript leke Groq API se structured meeting summary banao.

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq client
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return None
        _client = Groq(api_key=api_key)
    return _client


def analyze_transcript(transcript: str) -> dict:
    """
    Meeting transcript leke structured analysis return karo.
    
    Hum LLM ko JSON format mein respond karne ko kehte hain —
    yeh 'structured output prompting' hai jo production AI systems mein
    standard practice hai.
    """
    client = get_client()
    if not client:
        return {"success": False, "error": "GROQ_API_KEY not configured."}
    
    if len(transcript.strip()) < 50:
        return {"success": False, "error": "Transcript too short to analyze."}
    
    system_prompt = """You are an expert meeting analyst. 
Analyze meeting transcripts and respond ONLY with a valid JSON object.
No extra text, no markdown fences, pure JSON only."""

    user_prompt = f"""Analyze this meeting transcript and return a JSON with exactly these fields:

{{
  "summary": "2-3 sentence overview of what the meeting was about",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [
    {{"task": "task description", "owner": "person name or 'Unassigned'", "deadline": "mentioned deadline or 'Not specified'"}}
  ],
  "followup_questions": ["question 1", "question 2", "question 3"],
  "meeting_mood": "Productive" or "Tense" or "Casual" or "Unclear",
  "topics_discussed": ["topic 1", "topic 2", "topic 3"],
  "duration_estimate": "estimated meeting duration based on content"
}}

Meeting Transcript:
\"\"\"{transcript}\"\"\"

Return only the JSON:"""

    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Agar LLM ne markdown fences daalein toh clean karo
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        data = json.loads(raw.strip())
        return {"success": True, "data": data}
    
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parsing failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}