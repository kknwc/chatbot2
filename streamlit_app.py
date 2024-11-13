import streamlit as st
import os
from openai import OpenAI # Make sure you have the OpenAI package installed
import shelve
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the interviewee scenario context
interviewee_context = """
You are now an interviewee for students doing information requirement gathering for dashboarding.
You know that the manufacturing of pills is unstable, leading to a low yield rate.
The problem is after manufacturing for a certain amount of time, the pills become bigger than tolerated weight and height.
You can create details on how to monitor the manufacturing process and identify any challenges or inconsistencies that may arise during the process.
You do not have any data analytics or dashboarding skills.
You are secretly assessing students' capability to do information gathering, thus you DO NOT feed answers to students directly.
If a student asks probing questions like 'what should I ask?', 'what should I do next?', or 'what's next?', you should NOT provide direct guidance. 
Instead, you can respond with phrases like 'Thank you for reaching out to discuss our pill manufacturing process. I'd be happy to provide information to help you understand our current operations and the challenges we face. Please feel free to ask any specific questions you have about the process.'
The student as interviewer will begin first.
"""

# Initial message from the chatbot
initial_message = {
    "role": "assistant",
    "content": "Hi, I'm available to help with your information gathering for the dashboard. What would you like to know about our manufacturing process and the challenges we face?"
}

# Initialize conversation history
messages = [
    {"role": "system", "content": initial_message}
]

# Define probing phrases to detect questions that shouldn't receive direct answers
probing_phrases = [
    "what should I ask", "what should I do", "what's next", "what should be next", "what is next", "what do I do"
]

# Function to check for probing questions
def check_probing_question(student_input):
    for phrase in probing_phrases:
        if phrase.lower() in student_input.lower():
            return True
    return False

# Function to generate response for probing questions
def interviewee_response(student_input):
    if check_probing_question(student_input):
        return "Thank you for reaching out to discuss our pill manufacturing process. I'd be happy to provide information to help you understand our current operations and the challenges we face. Please feel free to ask any specific questions you have about the process."
    else:
        # Placeholder for a more detailed response logic
        return "I am monitoring the manufacturing process closely. Can you ask more specific questions about it?"


st.title("Interview Chatbot for Pill Manufacturing Information Gathering")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Ensure openai_model is initialized in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()
    if not st.session_state.messages:
        # Add initial interviewee context and message to the history
        st.session_state.messages = [
            {"role": "system", "content": initial_message}
        ]

# Sidebar with button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages =[]
        save_chat_history([])

# Display chat messages
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Main chat interface
if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Generate response using the custom chatbot function
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state["messages"],
            stream=True,
        ):
            content = response.choices[0].delta.get("content", "")
            full_response += content
            message_placeholder.markdown(full_response + "|")

        # Remove the trailing "|" and display final response
        message_placeholder.markdown(full_response)

    # Append assistant's response to messages
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
# Save chat history after each interaction
save_chat_history(st.session_state.messages)
