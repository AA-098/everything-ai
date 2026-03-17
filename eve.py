import os
import streamlit as st
import requests
import google.generativeai as genai

# Optional imports for local-only features
try:
    import wikipedia
except ModuleNotFoundError:
    wikipedia = None

try:
    import speech_recognition as sr
except ModuleNotFoundError:
    sr = None

try:
    import pyttsx3
    import threading, queue
except ModuleNotFoundError:
    pyttsx3 = None

# -------------------------
# CONFIG - Replace with your keys
# -------------------------
GEN_API_KEY = "AIzaSyC7cidb9VRwcHKIN6R-Kk1DkmfQjQfSdik"
GOOGLE_API_KEY = "AIzaSyC5PcMdpDmrBamGJxonvuhuLfRAeiWaQys"
CX_ID = "YOUR_CX_ID"

genai.configure(api_key=GEN_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------
# TTS ENGINE (local only)
# -------------------------
USE_TTS = pyttsx3 is not None and "STREAMLIT_SERVER_PORT" not in os.environ

if USE_TTS:
    engine = pyttsx3.init()
    speech_queue = queue.Queue()

    def _speech_worker():
        while True:
            text = speech_queue.get()
            if text is None:
                break
            engine.say(text)
            engine.runAndWait()
            speech_queue.task_done()

    threading.Thread(target=_speech_worker, daemon=True).start()

    def speak(text):
        speech_queue.put(text)
else:
    def speak(text):
        pass  # TTS disabled in cloud

# -------------------------
# GOOGLE SEARCH FUNCTION
# -------------------------
def google_search(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": GOOGLE_API_KEY, "cx": CX_ID, "q": query}
        response = requests.get(url, params=params).json()
        results = [item["snippet"] for item in response.get("items", [])[:5]]
        return "\n".join(results)
    except Exception:
        return ""

# -------------------------
# WIKIPEDIA SEARCH FUNCTION
# -------------------------
def wiki_search(query):
    if not wikipedia:
        return None
    try:
        return wikipedia.summary(query, sentences=3)
    except Exception:
        return None

# -------------------------
# MAIN AI FUNCTION
# -------------------------
def ask_ai(question):
    wiki = wiki_search(question)
    google_results = "" if wiki else google_search(question)

    prompt = f"""
    Question: {question}

    Wikipedia info:
    {wiki if wiki else 'None'}

    Google snippets:
    {google_results if google_results else 'None'}

    Provide a detailed, clear answer combining the information above.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI generation failed: {e}"

# -------------------------
# VOICE INPUT (local only)
# -------------------------
def voice_input():
    if not sr:
        st.warning("Voice input is not available in this environment.")
        return

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening...")
            audio = r.listen(source)
        text = r.recognize_google(audio)
        st.success(f"You said: {text}")
        answer = ask_ai(text)
        st.markdown("### 🤖 Everything AI Answer")
        st.write(answer)
        speak(answer)
    except Exception:
        st.error("Voice not recognized or microphone not available!")

# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Everything AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
body {background-color: black; color: white;}
.stApp {background-color: black; color: white;}
input, textarea, button {background-color: #222 !important; color: white !important;}
h1, h2, h3 {color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🌌 Everything AI")
st.caption("Created by Aarav Narwal")

# -------------------------
# TEXT INPUT FORM
# -------------------------
with st.form(key='ask_form', clear_on_submit=True):
    user_question = st.text_input("Ask Everything AI")
    submitted = st.form_submit_button("Ask")
    if submitted and user_question:
        answer = ask_ai(user_question)
        st.markdown("### 🤖 Everything AI Answer")
        st.write(answer)
        speak(answer)

# -------------------------
# VOICE INPUT BUTTON
# -------------------------
if st.button("🎤 Voice Question"):
    voice_input()
