import requests
from config import BASE_URL


embedding_model = "nomic-embed-text"


def get_embedding(text):

    response = requests.post(
        f"{BASE_URL}/api/embeddings",
        json={
            "model": embedding_model,
            "prompt": text
        }
    )

    data = response.json()


    return data["embedding"]