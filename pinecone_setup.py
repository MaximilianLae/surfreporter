import json
import os
from pinecone import Pinecone, ServerlessSpec
from config import PINECONE_API_KEY, GOOGLE_API_KEY

with open("..data/surf_spots_enriched.json", "r") as file:
    surf_spots = json.load(file)

spot_data = [
    {
        "spot_id": str(index + 1),
        "name": spot["url"].split("/")[-2],  # Extract name from URL
        "description": spot["details"]["Spot Description"],
        "metadata": {
            "direction_of_wave": spot["details"]["Direction of Wave"],
            "type_of_bottom": spot["details"]["Type of Bottom"],
        }
    }
    for index, spot in enumerate(surf_spots)
]

pinecone = Pinecone(
    api_key=PINECONE_API_KEY
)

index_name = "surfspots"

if index_name not in pinecone.list_indexes().names():
    pinecone.create_index(
        name=index_name,
        dimension=768,  # dimension for embedding model
        metric="cosine",  # cosine similarity for semantic search
        spec=ServerlessSpec(
            cloud="aws",  
            region="us-east-1"  
        )
    )

# Connect to the index
index = pinecone.Index(index_name)

from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

for spot in spot_data:
    print(f"Embedding and storing: {spot['name']}")
    vector = embeddings.embed_query(spot["description"])  
    index.upsert(
        vectors=[{
            "id": spot["spot_id"],  # Unique ID
            "values": vector,       # Embedding vector
            "metadata": {
                "name": spot["name"],  # Spot name
                "direction_of_wave": spot["metadata"]["direction_of_wave"],
                "type_of_bottom": spot["metadata"]["type_of_bottom"],
                "spot_description": spot["description"]  
            }
        }]
    )

print("All spot descriptions embedded and stored.")