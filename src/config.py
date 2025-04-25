import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()  

# Access variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
IPMA_API_KEY = os.getenv("IPMA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")