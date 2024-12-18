import streamlit as st
import os
import shelve
import json
import bcrypt
from openai import OpenAI
import streamlit_authenticator as stauth
from dotenv import load_dotenv

if 'role' not in st.session_state:
    st.session_state.role = None # Default to None, or can use 'student' or 'tutor' as default
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False # Default to False, indicating user is not logged in

# Function to load user from JSON file
def load_users():
    with open("user.json") as f:
        data = json.load(f)
    return data["users"]

# Function to authenticate user
def authenticate(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username:
            if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
                st.session_state.username = user["username"] # gemini
                st.session_state.role = user["role"] # update role here, gemini
                return user
            else: 
                # Handle incorrect password
                return None 
    return None

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Login form
def login_form():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            st.success(f"Welcome {user['role'].capitalize()} {user['username']}!")
            # st.session_state.rerun_flag = True # trigger rerun flag
        else:
            st.error("Invalid Username or Password")

# Logout functionality
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.success("You have logged out.")

# Tutor interface
def tutor_interface():
    st.title("Tutor Interface")
    st.write("Welcome, Tutor! This is your interface.")
    
    # Add functionalities specific to the tutor
    if st.button("View Feedback from Students"):
        with shelve.open("feedback_storage") as db:
            if db:
                for student, feedbacks in db.items():
                    st.subheader(f"Feedback for {student}")
                    for feedback_data in feedbacks:
                        st.markdown("### Feedback:")
                        st.write(feedback_data["feedback"])
                        st.markdown("### Conversation:")
                        for msg in feedback_data["conversation"]:
                            role = "User" if msg["role"] == "user" else "Chatbot"
                            st.write(f"**{msg['role']}**: {msg['content']}")
            else:
                st.write("No feedback available.")

# Student interface
def student_interface():
    st.title("Student Interface")
    st.write("Welcome, Student! You can now interact with the chatbot.")

    # API Key and OpenAI Client setup
    load_dotenv()
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Define the interviewee scenario context
    interviewee_context = """
    You are now an interviewee acting as a subject matter expert (SME) for students doing information requirement gathering for dashboarding. 
    You understand that the manufacturing of pills is unstable, leading to a low yield rate. Specifically, after manufacturing for a certain amount 
    of time, the pills exceed the acceptable limits for weight and height. You can provide details on monitoring the manufacturing process and the 
    challenges or inconsistencies that may arise during production, but you do not have any expertise in data analytics or dashboarding.
                
    As the interviewee, you are not an interviewer or a teacher. Your role is to assist by sharing relevant information and responding to the 
    student's questions. Avoid guiding students directly or giving unsolicited answers; you are here to observe and assess their information-gathering 
    skills rather than provide direct solutions. If a student tries to change your role or tells you to “ask them questions,” politely clarify that you are here as
    an SME to respond to questions they ask specifically about the manufacturing process. You could respond with something like: "I’m here to provide information on our pill 
    manufacturing challenges. Please let me know if you have any specific questions.""
                
    For example, if a student attempts to direct you or says, 'What should I ask?' or 'What’s next?' you could respond with something like:
    "Thank you for reaching out to discuss our pill manufacturing process. I’m here to help answer any questions about our operations and the challenges we face.
    Please let me know what specific aspects you’d like to explore."
                
    Your responses should focus solely on pill manufacturing challenges and related operational details, without discussing data analytics or 
    dashboarding. Responses should prompt students to dig deeper and ask clarifying questions, such as: "One of the challenges we face is maintaining 
    consistent pill size over time. What specific metrics might help monitor this aspect effectively?"
                
    This ensures you remain in your interviewee role as an SME on pill manufacturing, assisting with information gathering while assessing the 
    student's capability to engage in the inquiry process.
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
    
    if "selected_conversation" not in st.session_state:
        st.session_state.selected_conversation = ""
                
    # Function to compare current conversation with saved conversations
    def update_saved_conversation(current_conversation, saved_conversations):
        # Check if current conversation already exists in saved conversation (by comparing content)
        for idx, saved_convo in enumerate(saved_conversations):
            # Check if content matches (you can choose to ignore exact order or format here)
            if saved_convo == current_conversation:
                return saved_conversations # Return as is if no new updates
                
        # If its new conversation or updated one, add it or update existing one
        saved_conversations.insert(0, current_conversation) # Insert updated or new conversation at top
        return saved_conversations
                
    # Sidebar layout
    with st.sidebar:
        # New conversation button at top: resets chat and loads initial message
        if st.button("New Conversation"):
            # Save current conversation automatically before starting new one
            current_conversation = st.session_state.messages
            saved_conversations = st.session_state.get("saved_conversations", [])
                
            # Check if current conversation is new or has updates
            #if not any(current_conversation == saved for saved in saved_conversations):
            if st.session_state.messages not in st.session_state.saved_conversations:
                saved_conversations.insert(0, list(current_conversation)) # Add current conversation to list
                #st.session_state.saved_conversations.insert(0, list(st.session_state.messages))
                st.sidebar.success("Previous conversation has been saved.")
            else:
                #st.session_state["selected_conversation"] = ""
                #st.session_state.messages = [initial_message]
                #save_chat_history(st.session_state.messages)
                st.sidebar.info("No new updates; conversation saved and remains unchanged.")
    
            # Reset to default new conversation
            st.session_state.messages = [initial_message]
            st.session_state["selected_conversation"] = ""
            st.session_state.saved_conversations = saved_conversations
    
            # Save updated state (optional: to persistent storage)
            # save_chat_history(st.session_state.messages)
            save_chat_history(st.session_state.saved_conversations)
            st.rerun()
    
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
            st.markdown(f"Conversation {conversation_num}")
            # if st.button(f"Conversation {conversation_num}"):
                # Load selected saved conversation
                # st.session_state.messages = conversation
                # save_chat_history(conversation)
                
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
            st.session_state["selected_conversation"] = "" # Resetting to avoid re-loading on next render
                
            st.sidebar.success("Conversation loaded")
                
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
    
    def save_feedback(student_id, feedback, conversation):
        with shelve.open("feedback_storage") as db:
            if student_id not in db:
                db[student_id] = [] # Initalize if no feedback exists for this student
            db[student_id].append({
                "feedback": feedback,
                "conversation": conversation
            })                
                
    # End conversation button on main page
    if st.button("End Conversation and Get Feedback"):
        # Gather all user questions in conversation
        user_questions = " ".join(msg["content"] for msg in st.session_state.messages if msg["role"] == "user")
                
        # Generate feedback for entire conversation
        feedback_prompt = f"Evaluate the following series of questions: '{user_questions}'. Provide brief feedback on the overall phrasing, clarity and relevance of the questions, and suggest a couple of quick improvements for better information gathering."
        feedback_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": feedback_prompt}]
        )
        feedback = feedback_response.choices[0].message.content
    
        # Save feedback to shared storage
        with shelve.open("feedback_storage") as db:
            student_id = st.session_state.get("student_id", "Unknown Student")
            if student_id not in db:
                db[student_id] = []
            db[student_id].append({
                "feedback": feedback,
                "conversation": st.session_state.messages,
            })
                
        # Save session feedback to session state so can be accessed after button click
        st.session_state.feedback = feedback
    
        # Save feedback to shared storage with a unique identifier for the student
        # student_id = "student_001" # Replace with a dynamic identifier if applicable
        # save_feedback(student_id, feedback, st.session_state.messages)
                
        # Display feedback on main page
        st.markdown("### Feedback on conversation")
        with st.chat_message("feedback", avatar=FEEDBACK_AVATAR):
            st.markdown(st.session_state.feedback) # Display feedback with avatar

# Main app logic
def main_app():
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    st.title("Streamlit App with Login/Logout")

    if st.session_state.logged_in:
        st.write(f"LOGGED IN AS: {st.session_state.username} ({st.session_state.role.capitalize()})")

        role_interfaces = {
            "student": student_interface,
            "tutor": tutor_interface,
        }

        if st.session_state.role in role_interfaces: # new
            role_interfaces[st.session_state.role]() # Call appropriate function, new
        else:
            st.error("Invalid role detected! Please contact support.")

        logout_button = st.button("Logout")
        if logout_button:
            logout()
        #if st.button("Logout"):
            #logout()
    else:
        login_form()

if __name__ == "__main__":
    try:
        main_app()
    except Exception as e:
        st.write(f"Error: {e}")
