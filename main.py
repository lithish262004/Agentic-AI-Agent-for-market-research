from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
from chromadb import Client
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Agentic RAG Ad Rewriter with KG, Feedback & Memory")

# --- Mistral API Key ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "kLyfZ8hTIU2r0JGpekrcdovkbHY9pyxr")

# --- ChromaDB setup ---
client = Client()
collection = client.get_or_create_collection("ad_examples")

# --- Sentence Transformer for embeddings ---
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# --- Request models ---
class AdRequest(BaseModel):
    text: str
    tone: str
    platform: str
    product_category: str
    user_intent: str

class FeedbackRequest(BaseModel):
    rewritten_text: str
    rating: int  # 1–5 scale
    original_text: str
    platform: str
    product_category: str
    user_intent: str
    examples_used: list

# --- Knowledge Graph ---
knowledge_graph = {
    "Platforms": {
        "Instagram": {"supported_creatives": ["Image", "Carousel"], "preferred_tones": ["fun", "catchy"]},
        "Facebook": {"supported_creatives": ["Text", "Image"], "preferred_tones": ["professional", "friendly"]},
        "LinkedIn": {"supported_creatives": ["Text", "Video"], "preferred_tones": ["professional", "informative"]}
    },
    "ProductCategories": {
        "Smartphones": {"popular_platforms": ["Instagram", "Facebook"]},
        "Headphones": {"popular_platforms": ["Instagram", "Facebook"]},
        "Laptops": {"popular_platforms": ["LinkedIn", "Facebook"]}
    },
    "UserIntents": {
        "Promote sale": {"recommended_tones": ["fun", "catchy", "urgent"]},
        "Brand awareness": {"recommended_tones": ["professional", "informative"]}
    }
}

# --- Feedback & Memory Stores ---
feedback_store = []
example_scores = {}  # {example_text: cumulative_rating}
memory_store = {}    # {key: [past_interactions]}

def add_to_memory(platform, product_category, user_intent, data):
    """Save feedback or rewrites into memory keyed by platform+category+intent."""
    key = f"{platform}_{product_category}_{user_intent}"
    if key not in memory_store:
        memory_store[key] = []
    memory_store[key].append(data)

def get_memory(platform, product_category, user_intent):
    """Retrieve past memory for context."""
    key = f"{platform}_{product_category}_{user_intent}"
    return memory_store.get(key, [])

# --- Add initial ad examples to ChromaDB ---
def populate_chroma():
    texts = [
        "Buy the new smartphone with amazing camera features!",
        "Upgrade your phone experience with sleek design and performance.",
        "Capture every moment with our high-resolution camera phone.",
        "Experience lightning-fast performance with the latest smartphone."
    ]
    metadatas = [
        {"platform": "Instagram"},
        {"platform": "Facebook"},
        {"platform": "Instagram"},
        {"platform": "Facebook"}
    ]
    
    if len(collection.get()['documents']) == 0:
        ids = [str(i) for i in range(len(texts))]
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        print("ChromaDB populated with initial ads.")

populate_chroma()

# --- Retrieve top-k examples from Chroma ---
def retrieve_examples(text, platform, max_k=5):
    query_emb = embedding_model.encode(text).tolist()
    top_k = 3 if len(text.split()) < 10 else max_k

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        where={"platform": platform}
    )

    examples = []
    if 'documents' in results and len(results['documents']) > 0:
        examples = [doc for doc in results['documents'][0] if doc]

    return examples

# --- Filter examples using Knowledge Graph ---
def filter_examples_by_kg(examples, platform, product_category, user_intent):
    platform_info = knowledge_graph["Platforms"].get(platform, {})
    category_info = knowledge_graph["ProductCategories"].get(product_category, {})
    intent_info = knowledge_graph["UserIntents"].get(user_intent, {})

    # Keep only examples relevant to the product's popular platforms
    filtered = [ex for ex in examples if platform in category_info.get("popular_platforms", [])]

    # Rank by tone preference
    preferred_tones = platform_info.get("preferred_tones", []) + intent_info.get("recommended_tones", [])
    ranked = sorted(filtered, key=lambda x: any(tone in x.lower() for tone in preferred_tones), reverse=True)

    # Rank also by example score (if available)
    ranked = sorted(ranked, key=lambda x: example_scores.get(x, 0), reverse=True)

    return ranked if ranked else examples  # fallback to original examples if none match

# --- Generate rewritten ad using Mistral ---
def generate_with_mistral(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-large-2411",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

# --- POST endpoint: Run agent ---
@app.post("/run-agent")
async def run_agent(request: AdRequest):
    # Retrieve examples
    examples = retrieve_examples(request.text, request.platform)
    examples = filter_examples_by_kg(
        examples,
        platform=request.platform,
        product_category=request.product_category,
        user_intent=request.user_intent
    )
    examples_text = "\n".join(examples) if examples else "No examples found."

    # Retrieve relevant memories
    past_memories = get_memory(request.platform, request.product_category, request.user_intent)
    memory_context = "\n".join([m["rewritten_text"] for m in past_memories[-3:]]) if past_memories else "No past rewrites available."

    # Build prompt with memory
    prompt = (
        f"You are an expert ad copywriter.\n"
        f"Rewrite the following ad text in a {request.tone} tone for {request.platform}.\n\n"
        f"User text: {request.text}\n\n"
        f"Example ad texts:\n{examples_text}\n\n"
        f"Past successful rewrites (for context):\n{memory_context}"
    )

    # Generate ad
    rewritten_text = generate_with_mistral(prompt)

    # Save the new rewrite to memory
    add_to_memory(request.platform, request.product_category, request.user_intent, {
        "original_text": request.text,
        "rewritten_text": rewritten_text,
        "examples_used": examples
    })

    return {
        "rewritten_text": rewritten_text,
        "examples_used": examples,
        "memory_used": memory_context
    }

# --- POST endpoint: Submit feedback ---
@app.post("/submit-feedback")
async def submit_feedback(feedback: FeedbackRequest):
    # Store feedback
    feedback_store.append(feedback.dict())

    # Update memory with feedback
    add_to_memory(feedback.platform, feedback.product_category, feedback.user_intent, feedback.dict())

    # Update example scores for adaptive ranking
    for ex in feedback.examples_used:
        example_scores[ex] = example_scores.get(ex, 0) + feedback.rating

    print(f"Received feedback: {feedback.rating} stars for '{feedback.rewritten_text}'")
    print("Updated example scores:", example_scores)

    return {"message": "Feedback recorded and added to memory!"}

# --- Root endpoint ---
@app.get("/")
def root():
    return {"message": "Agentic RAG Ad Rewriter with KG, Feedback & Memory is running!"}
