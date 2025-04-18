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

    # Greeting
    greetings = ["hello", "good morning", "good afternoon", "good evening", "hi", "namaste"]
    if any(transcription_lower.startswith(greet) for greet in greetings):
        score += 20
        feedback.append("The call began with a proper greeting, which sets a professional and courteous tone for the customer interaction.")
    else:
        feedback.append("The call did not begin with a clear or polite greeting. A warm opening such as 'Good morning' or 'Hello' helps establish rapport.")

 
    for intent, keywords in intent_keywords.items():
        if any(keyword in transcription_lower for keyword in keywords):
            found_intents.append(intent)

    if found_intents:
        score += 20
        for intent in found_intents:
            feedback.append(f"The customer's intent was successfully identified and addressed: {intent}. This shows good listening and understanding.")
    else:
        feedback.append("The customer's intent was not clearly identified during the call. Proactively confirming their needs could improve communication.")


    positives = ["thank you", "sure", "absolutely", "happy to help", "zarur", "dhanyavaad"]
    if any(word in transcription_lower for word in positives):
        score += 20
        feedback.append("Positive and supportive language was used effectively, making the conversation feel pleasant and helpful.")
    else:
        feedback.append("There was a noticeable lack of positive or affirming phrases. Consider using encouraging words to build trust and satisfaction.")

    try:
        sentiment = TextBlob(transcription).sentiment.polarity
        if sentiment > 0:
            score += 20
            tone = "positive"
            feedback.append("The overall tone of the conversation was friendly and constructive, which greatly enhances customer satisfaction.")
        elif sentiment < 0:
            tone = "rude"
            feedback.append("The tone of the conversation appeared to be negative. Try to remain calm, respectful, and solution-focused, even during tough calls.")
        else:
            score += 10  
            tone = "neutral"
            feedback.append("The overall tone was neutral. While not necessarily bad, adding more warmth and engagement can leave a better impression.")
    except:
        tone = "unknown"
        feedback.append("Sentiment analysis could not be performed. Ensure the audio is clear and language is supported.")

    if tone == "rude":
        feedback.append("Due to the negative tone of the conversation, the ending statement has not been considered for evaluation.")
    elif any(closing in transcription_lower for closing in ["thank you", "bye", "have a nice day", "shukriya", "alvida"]):
        if tone == "neutral":
            feedback.append("The call ended with a proper closing, but since the tone of the conversation was neutral, the effectiveness of the closing is not fully credited.")
        else:
            score += 20
            feedback.append("The call concluded with a clear and polite closing statement, which helps leave a positive lasting impression.")
    else:
        if tone == "neutral":
            feedback.append("The conversation tone was neutral, and no clear closing was observed. A proper farewell helps to wrap up calls professionally.")
        else:
            feedback.append("A closing statement was missing. Always ensure to conclude with a polite goodbye to maintain professionalism.")

    return min(score, 100), "\n\n".join(feedback)

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

# Streamlit UI
st.title("Call Evaluation System")
st.markdown("Upload a call recording and click 'Evaluate Call' to analyze it and get personalized feedback.")

uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    base_name = os.path.splitext(uploaded_file.name)[0]
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.button("Evaluate Call"):
        with st.spinner("Transcribing and analyzing..."):
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
