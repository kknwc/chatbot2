import streamlit as st
import os
import shelve
import json
import bcrypt
from openai import OpenAI
import streamlit_authenticator as stauth

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
                            st.write(f"**{msg['role']}**: {msg['content']}")
            else:
                st.write("No feedback available.")

# Student interface
def student_interface():
    st.title("Student Interface")
    st.write("Welcome, Student! You can now interact with the chatbot.")

    # API Key and OpenAI Client setup
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

    # Define the chatbot scenario
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

    initial_message = {
        "role": "assistant",
        "content": "Hi, I'm available to help with your information gathering for the dashboard. What would you like to know about our manufacturing process and the challenges we face?"
    }

    USER_AVATAR = "👤"
    BOT_AVATAR = "🤖"

    # Chat history management
    def load_chat_history():
        with shelve.open("chat_history") as db:
            return db.get("messages", [])

    def save_chat_history(messages):
        with shelve.open("chat_history") as db:
            db["messages"] = messages

    # Initialize or load chat history
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()
        if not st.session_state.messages:
            st.session_state.messages = [initial_message]

    # Display chat messages
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("How can I help?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        # Generate response from OpenAI
        api_messages = [{"role": "system", "content": interviewee_context}] + st.session_state.messages
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ""

            for response in client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                stream=True,
            ):
                content = response.choices[0].delta.content or ""
                full_response += content
                message_placeholder.markdown(full_response + "|")

            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat_history(st.session_state.messages)

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
