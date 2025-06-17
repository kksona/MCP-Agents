import streamlit as st
import requests
import json
import os
import uuid
import time
import base64 # Import base64
from urllib.parse import urlparse # Import urlparse
from mimetypes import guess_type # Import guess_type
import re # Already imported, just for clarity

# Set page config
st.set_page_config(
    page_title="Image Agent Chat",
    page_icon="🔊",
    layout="centered"
)

# --- Configuration ---
API_SERVER_URL = "http://localhost:8000"
APP_NAME = "search"
USER_ID = "u_123" # Consider making USER_ID dynamic if multiple users will use this app
SESSION_ID = "s_123" # This is a fixed session ID. For a multi-user app, you might want to generate this per user/session.

# --- Endpoints ---
SESSION_CREATE_ENDPOINT = f"{API_SERVER_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
SESSION_DELETE_ENDPOINT = f"{API_SERVER_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
RUN_ENDPOINT = f"{API_SERVER_URL}/run"

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Re-using your robust backend functions ---

# Ensure these imports are at the top of your file for the functions to work
# import base64
# from urllib.parse import urlparse
# from mimetypes import guess_type
# import re
# (They are already there in your provided code, just making a note)

def create_session():
    """Handles the creation or update of a session."""
    st.info(f"Attempting to create/update session '{SESSION_ID}' for user '{USER_ID}'...")
    headers = {"Content-Type": "application/json"}
    payload = {"state": {"key1": "value1", "key2": 42}}

    try:
        response = requests.post(SESSION_CREATE_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        st.success(f"Session '{SESSION_ID}' created/updated successfully.")
        st.session_state.session_id = SESSION_ID
        st.session_state.messages = [] # Clear messages on new session
        return True
    except requests.exceptions.ConnectionError:
        st.error(f"Error: Could not connect to the ADK API server at {API_SERVER_URL}.")
        st.error("Please ensure 'adk api_server [your_agent_module_path]' is running in a separate terminal.")
        return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409: # Conflict means session already exists, which is fine for 'update'
            st.info(f"Session '{SESSION_ID}' already exists. Continuing with existing session.")
            st.session_state.session_id = SESSION_ID # Ensure session_id is set
            return True
        st.error(f"HTTP Error creating session: {e}")
        st.error(f"Response content: {e.response.text}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during session creation: {e}")
        return False

# Your existing get_image_base64_from_local_path function
def get_image_base64_from_local_path(image_path: str, mime_type: str = None) -> tuple[str, str | None]:
    """Reads a local image file and returns its Base64 encoded string and determined MIME type."""
    try:
        # In a Streamlit app, this function is usually called with st.file_uploader content,
        # not a disk path. Adjusting for future consideration if needed.
        # For now, it's used as a placeholder if you were to manually provide a local path.
        if not os.path.exists(image_path):
            st.warning(f"Error: Local image file not found at {image_path}. This function is usually for server-side paths.")
            return None, None

        if mime_type is None:
            guessed_mime, _ = guess_type(image_path)
            mime_type = guessed_mime if guessed_mime and guessed_mime.startswith('image/') else "image/jpeg"

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string, mime_type
    except Exception as e:
        st.error(f"Error encoding local image '{image_path}': {e}")
        return None, None

# Your existing get_image_base64_from_url function
def get_image_base64_from_url(image_url: str) -> tuple[str, str | None]:
    """
    Downloads an image from a URL, converts it to Base64, and determines its MIME type.
    Returns (base64_string, mime_type) or (None, None) on failure.
    """
    st.info(f"Attempting to download image from: {image_url}")
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        mime_type = response.headers.get('Content-Type')
        if not mime_type or not mime_type.startswith('image/'):
            parsed_url = urlparse(image_url)
            path_basename = os.path.basename(parsed_url.path)
            guessed_mime, _ = guess_type(path_basename)
            mime_type = guessed_mime if guessed_mime and guessed_mime.startswith('image/') else "image/jpeg"

        image_data = response.content
        encoded_string = base64.b64encode(image_data).decode('utf-8')
        st.success(f"Successfully downloaded and encoded image (MIME: {mime_type}).")
        return encoded_string, mime_type

    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading image from URL '{image_url}': {e}")
        return None, None
    except Exception as e:
        st.error(f"An unexpected error occurred while processing image URL '{image_url}': {e}")
        return None, None

# Your existing send_message_to_agent function
def send_message_to_agent(message: str, encoded_image_data: str = None, mime_type: str = None) -> str:
    """
    Sends a user message (and optionally Base64 image data)
    to the ADK agent via the /run endpoint and returns the agent's response.
    Note: This version directly accepts encoded_image_data and mime_type.
    """
    headers = {"Content-Type": "application/json"}
    parts = []

    if message:
        parts.append({"text": message})

    if encoded_image_data and mime_type:
        parts.append({
            "inlineData": {
                "mimeType": mime_type,
                "data": encoded_image_data
            }
        })
    elif encoded_image_data: # If data exists but mime_type is missing
        st.warning("Image data provided but MIME type is missing. Skipping image.")

    if not parts:
        return "Error: No content provided to send to the agent (message or image)."

    payload = {
        "appName": APP_NAME,
        "userId": USER_ID, # Use fixed USER_ID as per your config
        "sessionId": SESSION_ID, # Use fixed SESSION_ID as per your config
        "newMessage": {
            "role": "user",
            "parts": parts
        }
    }

    try:
        response = requests.post(RUN_ENDPOINT, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        response_data = response.json()

        if isinstance(response_data, list) and len(response_data) > 0:
            first_event = response_data[0]

            if 'content' in first_event and \
               'parts' in first_event['content'] and \
               isinstance(first_event['content']['parts'], list) and \
               len(first_event['content']['parts']) > 0:

                for part in first_event['content']['parts']:
                    if 'text' in part:
                        return part['text']

        return "Agent did not return a readable text response in the expected format."

    except requests.exceptions.ConnectionError:
        st.error(f"Error: Could not connect to the ADK API server at {API_SERVER_URL}.")
        st.error("Please ensure 'adk api_server [your_agent_module_path]' is running.")
        return "Connection error: Please ensure the ADK API server is running."
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error sending message: {e}")
        st.error(f"Response content: {e.response.text}")
        return f"Error communicating with agent: {e.response.text}"
    except Exception as e:
        st.error(f"An unexpected error occurred while sending message: {e}")
        return "An internal error occurred."


# --- Streamlit UI ---
st.title("Image Agent Chat")

# Sidebar for session management
with st.sidebar:
    st.header("Session Management")

    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session", key="new_session_button"):
            create_session()
            st.rerun() # Rerun to update UI after session creation
    else:
        st.warning("No active session")
        if st.button("➕ Create Session", key="create_session_button"):
            create_session()
            st.rerun() # Rerun to update UI after session creation

    st.divider()
    st.caption("This app interacts with the Image Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Chat interface
st.subheader("Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
            if "image_url" in msg and msg["image_url"]:
                st.image(msg["image_url"], caption="User Provided Image", width=200) # Display URL image
            elif "image_data" in msg and msg["image_data"]: # For local uploads
                 st.image(msg["image_data"], caption="User Provided Image", width=200)
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

# Input for new messages and image URL
if st.session_state.session_id:  # Only show input if session exists
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            user_message = st.text_input("Type your message...", key="user_message_input")
        with col2:
            image_url_input = st.text_input("Or paste Image URL", key="image_url_input")

        # Streamlit file uploader for local images (optional, but good practice for web apps)
        uploaded_file = st.file_uploader("Or upload an image", type=["jpg", "jpeg", "png"], key="image_uploader")

        submit_button = st.form_submit_button("Send")

        if submit_button and (user_message or image_url_input or uploaded_file):
            encoded_image_data = None
            mime_type = None
            display_image_url = None # To store URL for display in chat history

            if image_url_input:
                encoded_image_data, mime_type = get_image_base64_from_url(image_url_input)
                display_image_url = image_url_input # Store URL for display

            elif uploaded_file:
                # Streamlit uploaded files come as BytesIO objects
                bytes_data = uploaded_file.getvalue()
                encoded_image_data = base64.b64encode(bytes_data).decode('utf-8')
                mime_type = uploaded_file.type
                display_image_url = uploaded_file # Streamlit handles displaying uploaded files directly

            # Add user message and image to history
            message_entry = {"role": "user", "content": user_message}
            if display_image_url:
                if isinstance(display_image_url, str): # It's a URL
                    message_entry["image_url"] = display_image_url
                else: # It's an uploaded file object
                    message_entry["image_data"] = display_image_url


            st.session_state.messages.append(message_entry)

            # Send message to agent
            with st.spinner("Agent thinking..."):
                agent_response = send_message_to_agent(user_message, encoded_image_data, mime_type)

            st.session_state.messages.append({"role": "assistant", "content": agent_response})
            st.rerun() # Rerun to display new messages
else:
    st.info("👈 Create a session to start chatting.")

# Initial session creation on first run if not already set
if st.session_state.session_id is None:
    create_session()
    if st.session_state.session_id: # Only rerun if session was successfully created
        st.rerun()