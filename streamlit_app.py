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

st.title("Interview Chatbot for Pill Manufacturing Information Gathering")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

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
        # Start with initial message only (do not display context)
        st.session_state.messages = [initial_message]

# Sidebar with button to delete chat history
with st.sidebar:
    if st.button("delete chat history"):
        st.session_state.messages =[]
        save_chat_history([])

    # Manual save current conversation & start a new one
    if st.button("save current conversation"):
        saved_conversations = st.session_state.get("saved_conversations", [])
        saved_conversations.insert(0, list(st.session_state.messages)) # Save current conversation
        st.session_state.saved_conversations = saved_conversations
        st.session_state.messages = [initial_message] # Reset chat for new conversation
        save_chat_history(st.session_state.messages)
        st.sidebar.success("conversation saved successfully!")

    # New conversation button: resets chat and loads initial message
    if st.button("new conversation"):
        # Save current conversation automatically before starting new one
        saved_conversations = st.session_state.get("saved_conversations", [])
        saved_conversations.insert(0, list(st.session_state.messages)) # Insert at beginning to maintain order
        st.session_state.saved_conversations = saved_conversations

        # Reset conversation to initial message
        st.session_state.messages = [initial_message] # Resets chat
        save_chat_history(st.session_state.messages) # Save empty conversation (or initial state)

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

    # Prepare messages for the OpenAI API call
    api_messages = [{"role": "system", "content": interviewee_context}] + st.session_state.messages

    # Generate response using the custom chatbot function
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        
        for response in client.chat.completions.create(
            model = "gpt-4o-mini",
            messages=api_messages,
            stream=True,
        ):
            content = response.choices[0].delta.content or ""
            full_response += content
            message_placeholder.markdown(full_response + "|")

        # Remove the trailing "|" and display final response
        message_placeholder.markdown(full_response)

    # Append assistant's response to messages
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# Display saved conversations in sidebar
with st.sidebar: 
    st.subheader("Saved Conversations")
    saved_conversations = st.session_state.get("saved_conversations", [])
    if saved_conversations:
        for idx, conversation in enumerate(saved_conversations):
            if st.button(f"Conversation {idx + 1}"):
                # Load selected saved conversation
                st.session_state.messages = conversation
                save_chat_history(conversation)
