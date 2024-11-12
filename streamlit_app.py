import streamlit as st
import os
import openai # Make sure you have the OpenAI package installed

# Define your API key here
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the interviewee scenario context, can improve this so that the prompts are more detailed. can change and edit this part for prompt v2
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

# Initialize the conversation with the interviewee starting
initial_message = {
    "role": "assistant",
    "content": (
        "Hi, I'm available to help with your information gathering for the dashboard. "
        "What would you like to know about our manufacturing process and the challenges we face?"
    ),
}

# Initialize conversation history
messages = [
    {"role": "system", "content": interviewee_context},
    initial_message,
]

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    messages.append({"role": "user", "content": user_input})
    
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    )
    assistant_response = ''  # Initialize the assistant's response
    for chunk in stream:
        content = getattr(chunk.choices[0].delta, 'content', '') or ''
        # Ensure content is a string and not None
        print(content, end='', flush=True)
        assistant_response += content  # Accumulate the content
    messages.append({"role": "assistant", "content": assistant_response})  # Use the accumulated response
    print()
    
# Define a list of probing phrases
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
    for phrase in probing_phrases:
        if phrase.lower() in student_input.lower():
            return True
    return False

# Chatbot's response logic
def interviewee_response(student_input):
    if check_probing_question(student_input):
        return "Thank you for reaching out to discuss our pill manufacturing process. I'd be happy to provide information to help you understand our current operations and the challenges we face. Please feel free to ask any specific questions you have about the process."
    else:
        # Add logic here for normal responses based on the interviewee_context
        return generate_interviewee_response(student_input)

# Function to generate interviewee's response (you can expand this based on your implementation)
def generate_interviewee_response(student_input):
    # Use the context to generate a relevant response
    # e.g., using GPT model or predefined responses
    return "I am monitoring the manufacturing process closely. Can you ask more specific questions about it?"


### Streamlit UI ###

def main():
    # Set up title and instructions
    st.title("Interview Chatbot for Pill Manufacturing Information Gathering")
    st.write("Ask the interviewee questions about pill manufacturing to gather information.")

    # Initialize chat history and states if not already in session_state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False  # Track if user initiated conversation

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        else:
            st.write(f"Interviewee: {message['content']}")

    # Input form for user's message
    user_input = st.text_input("You:", key="user_input")

    # User clicks "Send" button to initiate conversation
    if st.button("Send") and user_input:
        # Append user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Start conversation with interviewee's initial message if not started yet
        if not st.session_state.conversation_started:
            st.session_state.messages.append(initial_message)
            st.session_state.conversation_started = True

        # Generate bot response
        response = interviewee_response(user_input)
        st.session_state.messages.append({"role": "assistant", "content": response})

       # Clear the user input field by refreshing its key with a new one
        st.experimental_rerun()

if __name__ == "__main__":
    main()
