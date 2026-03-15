import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = '''
You are Allen, the AI navigation assistant for AllWays Ottawa.
AllWays Ottawa is an accessible urban navigation app that scores routes on 4 dimensions:
  - safety (0-1): collision zones, traffic volume
  - accessibility (0-1): sidewalk quality, curb cuts, ramps
  - environment (0-1): air quality, parks and green corridors
  - comfort (0-1): nearby benches, washrooms, libraries, services

When the user describes their routing preference, you must:
1. Extract weights between 0.0 and 1.0 for each of the 4 dimensions
2. Write a short friendly explanation (1-2 sentences) of what route you are recommending

ALWAYS respond with ONLY valid JSON in this exact format, nothing else:
{
  "weights": {
    "safety": 0.5,
    "accessibility": 0.5,
    "environment": 0.5,
    "comfort": 0.5
  },
  "explanation": "One or two sentences explaining the route choice."
}

Examples:
User: 'I need a safe route, I have anxiety in heavy traffic'
Response: {"weights":{"safety":0.9,"accessibility":0.5,"environment":0.5,"comfort":0.7},"explanation":"I've prioritized quiet streets away from heavy traffic. This route avoids the busiest intersections and includes rest stops along the way."}

User: 'I use a wheelchair'
Response: {"weights":{"safety":0.7,"accessibility":0.95,"environment":0.4,"comfort":0.8},"explanation":"I've maximized accessibility on this route — it follows sidewalks with curb cuts and avoids uneven surfaces. Benches are available if you need a rest."}
'''

def chat_with_allen(user_message: str, conversation_history: List[Dict] = None) -> Dict:
    """
    Send a message to Allen and get back routing weights + explanation.
    conversation_history is a list of {role, content} dicts for multi-turn.
    """
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history[-6:])  # keep last 3 turns
    messages.append({'role': 'user', 'content': user_message})

    response = client.chat.completions.create(
        model='gpt-4o-mini',  # cheap and reliable for JSON extraction
        messages=messages,
        max_tokens=300,
        temperature=0.3,  # low temperature = more consistent JSON output
        response_format={'type': 'json_object'},  # forces JSON output
    )
    content = response.choices[0].message.content
    parsed = json.loads(content)

    # Validate structure
    if 'weights' not in parsed or 'explanation' not in parsed:
        raise ValueError('Allen returned unexpected JSON structure')

    return {
        'weights':     parsed['weights'],
        'explanation': parsed['explanation'],
        'message':     {'role': 'assistant', 'content': content}  # for history
    }