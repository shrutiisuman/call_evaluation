import os
import whisper
from gtts import gTTS
from textblob import TextBlob
import streamlit as st

model = whisper.load_model("base")

UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripts"
SCORE_FOLDER = "scores"
FEEDBACK_TEXT_FOLDER = "feedback_text"
AUDIO_FEEDBACK_FOLDER = "static/feedback_audio"

for folder in [UPLOAD_FOLDER, TRANSCRIPT_FOLDER, SCORE_FOLDER, FEEDBACK_TEXT_FOLDER, AUDIO_FEEDBACK_FOLDER]:
    os.makedirs(folder, exist_ok=True)

intent_keywords = {
    "refund": ["refund", "money back", "return"],
    "cancellation": ["cancel", "terminate", "end service"],
    "onboarding": ["start", "setup", "onboarding"],
    "support": ["help", "support", "issue", "problem", "trouble"],
    "billing": ["charge", "billing", "invoice", "payment"],
}

def evaluate_call(transcription):
    score = 0
    feedback = []
    transcription_lower = transcription.lower()
    found_intents = []

    greetings = ["hello", "good morning", "good afternoon", "good evening", "hi", "namaste"]
    if any(transcription_lower.startswith(greet) for greet in greetings):
        score += 20
        feedback.append("The call started with a proper greeting, which sets a positive tone.")
    else:
        feedback.append("The call did not start with a recognizable greeting. Consider starting with a professional greeting like 'Good morning' or 'Hello'.")

    for intent, keywords in intent_keywords.items():
        if any(keyword in transcription_lower for keyword in keywords):
            found_intents.append(intent)

    if found_intents:
        score += 20
        feedback.append(f"The intent of the customer was successfully identified as related to: {', '.join(found_intents)}.")
    else:
        feedback.append("The call did not clearly identify the customer's intent. Listening carefully and confirming their need would help.")

    positives = ["thank you", "sure", "absolutely", "happy to help", "zarur", "dhanyavaad"]
    if any(word in transcription_lower for word in positives):
        score += 20
        feedback.append("The use of positive and affirming language contributes to a better customer experience.")
    else:
        feedback.append("There was a lack of positive phrases. Using reassuring language helps build rapport.")

    if any(closing in transcription_lower for closing in ["thank you", "bye", "have a nice day", "shukriya", "alvida"]):
        score += 20
        feedback.append("The call ended with a proper closing, which leaves a good final impression.")
    else:
        feedback.append("A closing statement was missing. Always end calls with a polite and clear farewell.")

    try:
        sentiment = TextBlob(transcription).sentiment.polarity
        if sentiment > 0:
            score += 20
            feedback.append("Overall tone of the conversation was positive, which is appreciated in customer interactions.")
        elif sentiment < 0:
            feedback.append("The tone seemed negative at times. Try to stay calm and constructive even in tough conversations.")
        else:
            feedback.append("The tone was neutral. Consider adding more warmth and engagement.")
    except:
        feedback.append("Sentiment analysis could not be performed on this transcription.")

    summary = "\n\n".join(feedback)
    return min(score, 100), summary

def save_text_file(text, folder, base_name):
    filename = f"{base_name}.txt"
    with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
        f.write(text)
    return filename

def generate_feedback_audio(text, base_name):
    filename = f"{base_name}.mp3"
    path = os.path.join(AUDIO_FEEDBACK_FOLDER, filename)
    tts = gTTS(text=text, lang='en')
    tts.save(path)
    return filename


st.title("Call Evaluation System")
st.markdown("Upload a call recording and click 'Evaluate Call' to analyze it.")

uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    base_name = os.path.splitext(uploaded_file.name)[0]
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Evaluate Call"):
        with st.spinner("Transcribing and evaluating..."):
            result = model.transcribe(file_path)
            transcription = result["text"]

            score, feedback_text = evaluate_call(transcription)

            save_text_file(transcription, TRANSCRIPT_FOLDER, base_name)
            save_text_file(str(score), SCORE_FOLDER, base_name)
            save_text_file(feedback_text, FEEDBACK_TEXT_FOLDER, base_name)

            feedback_audio_file = generate_feedback_audio(feedback_text, base_name)
            feedback_audio_path = os.path.join(AUDIO_FEEDBACK_FOLDER, feedback_audio_file)


        st.subheader(f"Score: {score}/100")
        st.write(feedback_text)

        st.subheader("Audio Feedback:")
        st.audio(feedback_audio_path)
