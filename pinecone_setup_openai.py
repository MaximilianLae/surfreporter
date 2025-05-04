import json
import openai
from pinecone import Pinecone, ServerlessSpec

# ─── Your API keys & config ────────────────────────────────────────────────
from config import PINECONE_API_KEY, OPENAI_API_KEY
PINECONE_ENV      = "us-east1-aws"              # or whatever your env is
INDEX_NAME        = "surfspots-openai-embedding"
DIMENSION         = 3072                        # for text-embedding-3-large

# ─── Initialize Pinecone client ─────────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(INDEX_NAME)

# ─── Configure OpenAI ───────────────────────────────────────────────────────
openai.api_key = OPENAI_API_KEY

# ─── Load & prepare your spot data ─────────────────────────────────────────
with open("C:/Users/laech/OneDrive/Documents/surfreporter/data/surf_spots_enriched.json", "r") as f:
    surf_spots = json.load(f)

spot_data = [
    {
        "spot_id":    str(i + 1),
        "name":       spot["url"].split("/")[-2],
        "description": spot["details"]["Spot Description"],
        "metadata": {
            "direction_of_wave": spot["details"]["Direction of Wave"],
            "type_of_bottom":    spot["details"]["Type of Bottom"],
        },
    }
    for i, spot in enumerate(surf_spots)
]

# ─── Batch‐embed all descriptions via OpenAI ────────────────────────────────
texts = [s["description"] for s in spot_data]
resp  = openai.embeddings.create(
    model="text-embedding-3-large",
    input=texts
)

# ─── Build upsert payload & write to Pinecone ──────────────────────────────
vectors = []
for spot, entry in zip(spot_data, resp.data):
    # entry.embedding is the 3072-dim list
    vector = entry.embedding  
    vectors.append({
        "id":       spot["spot_id"],
        "values":   vector,
        "metadata": {
            "name":               spot["name"],
            "direction_of_wave":  spot["metadata"]["direction_of_wave"],
            "type_of_bottom":     spot["metadata"]["type_of_bottom"],
            "spot_description":   spot["description"],
        }
    })

index.upsert(vectors=vectors)
print(f"✅ Upserted {len(vectors)} vectors into '{INDEX_NAME}'.")