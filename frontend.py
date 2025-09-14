import streamlit as st
import requests
import json

# FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Agentic RAG Ad Rewriter", layout="wide")
st.title("🎯 Agentic RAG Ad Rewriter with KG, Feedback & Memory")

# --- Sidebar API Explorer ---
st.sidebar.title("⚙️ API Explorer")
api_choice = st.sidebar.radio("Choose Endpoint", ["Run Agent", "Submit Feedback"])

st.sidebar.markdown("---")

# --- Run Agent Section ---
if api_choice == "Run Agent":
    st.subheader("🚀 Run Agent")
    
    text = st.text_area("Text", "Check out our new wireless headphones with noise cancellation.")
    tone = st.selectbox("Tone", ["fun", "professional", "catchy", "informative"])
    platform = st.selectbox("Platform", ["Instagram", "Facebook", "LinkedIn"])
    product_category = st.selectbox("Product Category", ["Smartphones", "Headphones", "Laptops"])
    user_intent = st.selectbox("User Intent", ["Promote sale", "Brand awareness"])
    
    if st.button("Send Request"):
        payload = {
            "text": text,
            "tone": tone,
            "platform": platform,
            "product_category": product_category,
            "user_intent": user_intent
        }
        st.code(json.dumps(payload, indent=2), language="json")  # show request body
        
        try:
            response = requests.post(f"{BACKEND_URL}/run-agent", json=payload)
            if response.status_code == 200:
                st.success("✅ Response from /run-agent")
                st.json(response.json())
                # Save last result in session state for feedback
                st.session_state["last_result"] = response.json()
            else:
                st.error(f"❌ {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"⚠️ Could not connect to backend: {e}")

# --- Submit Feedback Section ---
elif api_choice == "Submit Feedback":
    st.subheader("⭐ Submit Feedback")
    
    last_result = st.session_state.get("last_result", None)
    
    if last_result:
        st.info("Prefilled from last agent run")
        rewritten_text = last_result.get("rewritten_text", "")
        examples_used = last_result.get("examples_used", [])
        original_text = st.text_area("Original Text", last_result.get("original_text", ""))
    else:
        st.warning("Run the agent first to prefill feedback fields")
        rewritten_text = st.text_area("Rewritten Text")
        original_text = st.text_area("Original Text")
        examples_used = st.text_area("Examples Used (comma separated)").split(",")
    
    rating = st.slider("Rating (1–5)", 1, 5, 3)
    platform = st.selectbox("Platform", ["Instagram", "Facebook", "LinkedIn"])
    product_category = st.selectbox("Product Category", ["Smartphones", "Headphones", "Laptops"])
    user_intent = st.selectbox("User Intent", ["Promote sale", "Brand awareness"])
    
    if st.button("Submit Feedback"):
        payload = {
            "rewritten_text": rewritten_text,
            "rating": rating,
            "original_text": original_text,
            "platform": platform,
            "product_category": product_category,
            "user_intent": user_intent,
            "examples_used": examples_used
        }
        st.code(json.dumps(payload, indent=2), language="json")  # show request body
        
        try:
            response = requests.post(f"{BACKEND_URL}/submit-feedback", json=payload)
            if response.status_code == 200:
                st.success("✅ Feedback submitted successfully")
                st.json(response.json())
            else:
                st.error(f"❌ {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"⚠️ Could not connect to backend: {e}")
