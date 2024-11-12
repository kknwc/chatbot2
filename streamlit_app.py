import streamlit as st
import os
from openai import OpenAI # Make sure you have the OpenAI package installed

# Define your API key here
#openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Interviewee context for GPT to understand the role and scenario
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

# Initialize conversation history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": interviewee_context},
        {"role": "assistant", "content": "Hi, I'm available to help with your information gathering for the dashboard. "}
    ]

# List of probing phrases that require indirect responses
probing_phrases = [
    "what should I ask",
    "what should I do",
    "what's next",
    "what should be next",
    "what is next",
    "what do I do"
]

# Function to check for probing questions
def check_probing_question(student_input):
    return any(phrase.lower() in student_input.lower() for phrase in probing_phrases)
    
# Function to generate response based on the context
def interviewee_response(student_input):
    if check_probing_question(student_input):
        return ("Thank you for reaching out to discuss our pill manufacturing process. "
                "I'd be happy to provide information to help you understand our current operations and the challenges we face. "
                "Please feel free to ask any specific questions you have about the process.")
    else:
        return generate_interviewee_response(student_input)

# Function to generate a response using OpenAI API
def generate_interviewee_response(student_input):
    st.session_state.messages.append({"role": "user", "content": student_input})
    response =  client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages,
    )
    assistant_response = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    return assistant_response

### Streamlit UI ###

def main():
    # Set up title and instructions
    st.title("Interview Chatbot for Pill Manufacturing Information Gathering")
    st.write("Ask the interviewee questions about pill manufacturing to gather information.")

    # Display chat history, skipping the "system" role message
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        elif message["role"] == "assistant":
            st.write(f"Interviewee: {message['content']}")

    # Input form for user's message
    with st.form(key="user_input_form", clear_on_submit=True):
        user_input = st.text_input("You:", key="user_input")
   
  # Submit button for sending user input
        submit_button = st.form_submit_button("Send")

        if submit_button and user_input:
            # Append user message to chat history
            #st.session_state.messages.append({"role": "user", "content": user_input})

            # Generate bot response
            response = interviewee_response(user_input)
            #st.session_state.messages.append({"role": "assistant", "content": response})

            # Refresh the app to display updated chat
            #st.experimental_rerun()

if __name__ == "__main__":
    main()
