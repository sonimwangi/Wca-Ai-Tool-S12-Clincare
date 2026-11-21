import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

from faq import faq_data
from memory import (
    conversation_memory,
    save_chat,load_chat_history
)
from summary import generate_summary

# ----------------------------
# PAGE SETUP 
# ----------------------------

st.set_page_config(
    page_title="Clinic Assistant",
    page_icon="🏥",
    layout="centered"
)

st.title("🏥 Clinic Assistant")

st.write(
    "Ask about clinic services, prices, bookings, and opening hours."
)

# ----------------------------
# DISPLAY OF SESSION MEMORY
# ----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ----------------------------
# LOAD GEMINI
# ----------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")



client = genai.Client(api_key=api_key)

# ----------------------------
# RESTRICTED MEDICAL WORDS
# ----------------------------

diagnosis_words = [
    "diagnosis",
    "diagnose",
    "disease",
    "illness",
    "condition",
    "what disease",
    "what condition",
]



#---------------------------
# USER INPUT
# ----------------------------

user_question = st.chat_input("Ask a clinic question...")

if user_question:

    # Display user message
    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    with st.chat_message("user"):
        st.write(user_question)

    q = user_question.lower()

    # ----------------------------
    # EXIT & SUMMARY
    # ----------------------------

    if q == "exit":
        

        summary= generate_summary(conversation_memory)
        st.subheader("Session Summary")
        st.text (summary)

        conversation_memory.clear()

        st.stop()

    answer = None
    # --------------------------
    # CHECK PREVIOUS/REPEATED QUESTIONS
    #-----------------------------
   

    for item in conversation_memory:

        if item["question"].strip().lower() == q:

            answer = (
                "You already asked this question.\n\n"
                f"Previous answer:\n{item['answer']}"
            )
            break
    # ----------------------------
    # NEW QUESTION PROCESSING
    # ----------------------------
    if answer is None:
    # Diagnosis refusal
        if any(word in q for word in diagnosis_words):

            answer = (
                "I cannot provide a diagnosis. "
                "Please consult a qualified healthcare professional."
            )
    #-----------------------------
            #FAQ LOOKUP
    #-----------------------------
    # Opening hours
        elif any(word in q for word in
                 ["hour", "hours", "open", "opening", "schedule"]):

            answer = faq_data["hours"]
    # Prices
        elif any(word in q for word in
                 ["price", "prices", "cost", "fee",
                  "consultation", "consultations"]):

            answer = faq_data["prices"]
    #Booking
        elif any(word in q for word in
                 ["book", "booking", "appointment",
                  "reserve", "schedule appointment"]):

            answer = faq_data["booking"]
    # Services

        elif any(word in q for word in
                 ["service", "services"]):

            answer = faq_data["services"]
        #-------------------------------
        # GEMINI FALLBACK
        #-------------------------------
        else:

            history = load_chat_history()


            

            prompt = f"""
You are a Clinic FAQ Assistant.

Clinic Information:

Opening/Working Hours:
{faq_data["hours"]}

Prices:
{faq_data["prices"]}

Booking:
{faq_data["booking"]}

Services:
{faq_data["services"]}
Previous conversation:
{history}

Rules:
1. Answer only clinic-related questions.
2. Remember previous questions.
3. Avoid repeating answers unnecessarily.
4. Never diagnose diseases.
5. Never prescribe medicine.
6. If a question is unrelated to clinic services, respond:
   "That is outside my field."
7. Use clinic information provided.
8. Never prescribe medication.
9. If asked for diagnosis, politely refuse.

Current Question:
{user_question}
"""

            try:

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt
                    )

                    answer = response.text

            except Exception as e:

                    answer = (
                        "This information is currently unavailable. Please try again in a moment, or contact the clinic directly for help.\n\n"
                        "Please ask about:\n"
                        "- Clinic services\n"
                        "- Prices\n"
                        "- Bookings\n"
                        "- Opening hours"
                    )

                    print("Error:", e)

    # ----------------------------
    #  STORE MEMORY
    # ----------------------------

        conversation_memory.append({
        "question": user_question,
        "answer": answer
    })

    save_chat(user_question, answer)

    # ----------------------------
    # DISPLAY ASSISTANT RESPONSE
    # ----------------------------

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    with st.chat_message("assistant"):
        st.write(answer)