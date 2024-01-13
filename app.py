 # Importing required packages
import streamlit as st
import openai
import uuid
import time
import pandas as pd
import io
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()
start_msg = "Hello there, human friends! I'm Cosmo, your furry AI Teaching Fellow for Harvard's CS 32 Course. Think of me as your digital tail-wagging guide, ready to fetch answers and help you paws your way through any tough spots in CS 32! Just a friendly reminder, though: I can't give out any solutions and I'm still learning to be a top dog in this AI world, so if you sniff out any discrepancies between what I say and the official course website or the wisdom of our human CS 32 Teaching Staff, trust their words over mine. Let's embark on this coding adventure together - with lots of treats and fun along the way! 🐾"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "run" not in st.session_state:
    st.session_state.run = {"status": None}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

# Set up the page
st.set_page_config(page_title="Cosmo - CS32 TF")

# Add custom CSS to hide the GitHub icon
css = """
#MainMenu, .stActionButton {
  visibility: hidden;
}
"""
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Initialize OpenAI assistant
if "assistant" not in st.session_state:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.assistant = openai.beta.assistants.retrieve(st.secrets["OPENAI_ASSISTANT"])
    st.session_state.thread = client.beta.threads.create(
        metadata={'session_id': st.session_state.session_id}
    )

# Display chat messages
elif hasattr(st.session_state.run, 'status') and st.session_state.run.status == "completed":
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread.id
    )
    for message in reversed(st.session_state.messages.data):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content_part in message.content:
                    message_text = content_part.text.value
                    st.markdown(message_text)

# Display the initial placeholder message from the assistant
if not st.session_state.messages:
    with st.chat_message('assistant', avatar="cosmo.png"):
        st.write(start_msg)
    st.session_state.messages.append(start_msg)

# Chat input and message creation
if prompt := st.chat_input("How can I help you?"):
    with st.chat_message('user'):
        st.write(prompt)

    with st.chat_message('assistant', avatar="cosmo.png"):
        st.write("Thinking ......")

    message_data = {
        "thread_id": st.session_state.thread.id,
        "role": "user",
        "content": prompt
    }
        
    st.session_state.messages = client.beta.threads.messages.create(**message_data)

    st.session_state.run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread.id,
        assistant_id=st.session_state.assistant.id,
    )

# Handle run status
if hasattr(st.session_state.run, 'status'):
    if st.session_state.run.status == "running":
        if st.session_state.retry_error < 3:
            time.sleep(1)
            st.rerun()

    elif st.session_state.run.status == "failed":
        st.session_state.retry_error += 1
        with st.chat_message('assistant', avatar="cosmo.png"):
            if st.session_state.retry_error < 3:
                st.write("Run failed, retrying ......")
                time.sleep(3)
                st.rerun()
            else:
                st.error("FAILED: The OpenAI API is currently processing too many requests. Please try again later ......")

    elif st.session_state.run.status != "completed":
        st.session_state.run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread.id,
            run_id=st.session_state.run.id,
        )
        if st.session_state.retry_error < 3:
            time.sleep(3)
            st.rerun()
