from google import genai
from dotenv import load_dotenv
import os
load_dotenv()
token = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=token)

def query(question):
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=question
    )
    return response.text