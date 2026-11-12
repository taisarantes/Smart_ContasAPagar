from dotenv import load_dotenv
import os

load_dotenv()

MODELO = os.getenv("LLM_MODELO")
BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")