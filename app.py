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
        feedback.append("The call started with a proper greeting, which helps set a professional and friendly tone at the beginning of the conversation. This is important for establishing rapport quickly.")
    else:
        feedback.append("The call did not start with a recognizable greeting. Starting with a professional greeting like 'Good morning' or 'Hello' helps in setting a positive tone from the beginning.")

    for intent, keywords in intent_keywords.items():
        if any(keyword in transcription_lower for keyword in keywords):
            found_intents.append(intent)

    if found_intents:
        score += 20
        feedback.append(f"The intent of the customer was successfully identified as related to: {', '.join(found_intents)}. This indicates active listening and understanding of the customer's needs.")
    else:
        feedback.append("The call did not clearly identify the customer's intent. It's important to listen carefully and ask clarifying questions to fully understand their needs.")

    positives = ["thank you", "sure", "absolutely", "happy to help", "zarur", "dhanyavaad"]
    if any(word in transcription_lower for word in positives):
        score += 20
        feedback.append("The use of positive and affirming language contributes to a better customer experience. It makes the interaction feel more supportive and professional.")
    else:
        feedback.append("There was a lack of positive phrases. Using encouraging and polite language helps in building trust and comfort with the customer.")

    sentiment = TextBlob(transcription).sentiment.polarity
    tone = "neutral"

    if sentiment > 0.2:
        score += 20
        tone = "positive"
        feedback.append("Overall tone of the conversation was positive, which is appreciated in customer interactions. Keep maintaining that friendly and enthusiastic tone.")
    elif sentiment < -0.1:
        tone = "rude"
        feedback.append("The tone of the conversation appeared negative or rude. It's important to remain calm, courteous, and constructive even when faced with difficult situations.")
    else:
        score += 10
        tone = "neutral"
        feedback.append("The tone was neutral throughout the call. While this is acceptable, adding some warmth and positive affirmations could make the interaction more pleasant.")

    if tone == "rude":
        feedback.append("Since the tone was identified as rude, we are skipping the evaluation of the call closing as tone significantly affects the overall experience.")
    else:
        if any(closing in transcription_lower for closing in ["thank you", "bye", "have a nice day", "shukriya", "alvida"]):
            score += 20
            feedback.append("The call ended with a proper closing, which leaves a good final impression. It's a small detail that reinforces professionalism and courtesy.")
        else:
            feedback.append("A closing statement was missing. Always end calls with a polite and clear farewell to leave a positive lasting impression.")

    if tone == "neutral":
        feedback.append("Your tone was identified as neutral, so the impact of the ending was not considered in the final scoring. Consider being slightly more positive to boost customer satisfaction.")

    summary = f"Tone detected: {tone.capitalize()}\n\n" + "\n\n".join(feedback)
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
