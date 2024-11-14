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
FEEDBACK_AVATAR = "📝"    
    
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

# Ensure saved_conversations is initialised in session state
if "saved_conversations" not in st.session_state:
    st.session_state.saved_conversations = []

# Sidebar layout
with st.sidebar:
    # New conversation button at top: resets chat and loads initial message
    if st.button("New Conversation"):
        # Save current conversation automatically before starting new one
        saved_conversations = st.session_state.get("saved_conversations", [])
        saved_conversations.insert(0, list(st.session_state.messages)) # Insert at beginning to maintain order
        st.session_state.saved_conversations = saved_conversations

        # Display success message
        st.sidebar.success("Previous conversation has been saved.")

        # Reset conversation to initial message
        st.session_state.messages = [initial_message] # Resets chat
        save_chat_history(st.session_state.messages) # Save empty conversation (or initial state)

    # Add spacing between buttons
    st.write("---")

    # Manual save current conversation & start a new one
    if st.button("Save Current Conversation"):
        saved_conversations = st.session_state.get("saved_conversations", [])
        saved_conversations.insert(0, list(st.session_state.messages)) # Save current conversation
        st.session_state.saved_conversations = saved_conversations
        st.session_state.messages = [initial_message] # Reset chat for new conversation
        save_chat_history(st.session_state.messages)
        st.sidebar.success("Conversation has been saved successfully!")

    # Display list of saved conversations with latest on top
    st.markdown("### Saved Conversations")
    saved_conversations = st.session_state.get("saved_conversations", [])
    for idx, conversation in enumerate(reversed(saved_conversations)):
        conversation_num = len(saved_conversations) - idx
        if st.button(f"Conversation {conversation_num}"):
            # Load selected saved conversation
            st.session_state.messages = conversation
            save_chat_history(conversation)

    # Display dropdown to select conversation to display
    st.markdown("### Select Conversation")
    num_conversations = len(st.session_state.saved_conversations)
    conversation_titles = [f"Conversation {i + 1}" for i in range(num_conversations)]
    # Display saved conversations as selectable options
    selected_conversation = st.selectbox(
        "Select a conversation to load:",
        options=[""] + list(reversed(conversation_titles)),
        index=0
    )

    # Check if conversation is selected from dropdown
    if selected_conversation and selected_conversation != "":
        # Find the index of the selected conversation
        conversation_index = num_conversations - int(selected_conversation.split(" ")[-1])

        # Load the selected conversation into the current messages
        st.session_state.messages = st.session_state.saved_conversations[conversation_index]
        save_chat_history(st.session_state.messages) # Save selected conversation to chat history

        # Refresh app by clearing 'selected_conversation' after loading messages
        st.session_state["selected_conversation"] = "" # Resetting to acoid re-loading on next render

    # Add spacing before delete button
    st.write("---")

    # Delete chat history button at bottom
    if st.button("Delete Chat History"):
        # Reset chat history to initial message
        st.session_state.messages =[initial_message]
        save_chat_history(st.session_state.messages)
        st.sidebar.success("Chat History has been deleted.")

        # Clear the saved conversations state to ensure its reflected immediately
        st.session_state.saved_conversations = []        

        if "selected_conversation" in st.session_state:
            del st.session_state["selected_conversation"]

        st.session_state["messages_reset"] = True

    if st.session_state.get("messages_reset", False):
        st.session_state["messages_reset"] = False

        # Refresh the app by triggering the change
        # st.write("") # This is a workaround for triggering an update

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

    # Generate feedback and display it
    # feedback = provide_feedback(prompt)
    # st.session_state.messages.append({"role": "feedback", "content": feedback})
    # with st.chat_message("feedback", avatar=FEEDBACK_AVATAR):
        # st.markdown(feedback)
        
# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# End conversation button on main page
# st.write("--")
if st.button("End Conversation and Get Feedback"):
    # Gather all user questions in conversation
    user_questions = " ".join(msg["content"] for msg in st.session_state.messages if msg["role"] == "user")

    # Generate feedback for entire conversation
    feedback_prompt = f"Evaluate the following series of questions: '{user_questions}'. Provide feedback on the overall phrasing, clarity, relevance, and suggest improvements for effective information gathering."
    feedback_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": feedback_prompt}]
    )
    feedback = feedback_response.choices[0].message.content

    # Save session feedback to session state so can be accessed after button click
    st.session_state.feedback = feedback

    # Display feedback on main page
    st.markdown("### Feedback on conversation")
    with st.chat_message("assistant", avatar=FEEDBACK_AVATAR):
        st.markdown(st.session_state.feedback) # Display feedback with avatar
