import streamlit as st
import requests
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="MLB Analytics AI",
    page_icon="⚾",
    layout="centered"
)

# Agent URL
AGENT_URL = os.environ.get('AGENT_URL', 'http://localhost:8080')
st.sidebar.markdown("### ⚙️ Agent Settings")
st.sidebar.markdown(f"**Agent URL:** `{AGENT_URL}`")

# Sidebar toggles
show_raw_json = st.sidebar.checkbox("📦 Show raw JSON response", value=False)
verbose_mode = st.sidebar.checkbox("🔁 Verbose logging", value=True)

# Session state
if 'session_id' not in st.session_state:
    session_id = f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.session_id = session_id
    st.session_state.session_created = False
    st.sidebar.markdown("### 🧾 Session Info")
    st.sidebar.markdown("🆕 **New Session Created:**")
    st.sidebar.code(session_id)
else:
    st.sidebar.markdown("### 🧾 Session Info")
    st.sidebar.markdown("📂 **Resuming Session:**")
    st.sidebar.code(st.session_state.session_id)


if 'messages' not in st.session_state:
    st.session_state.messages = []

# Title and UI header
st.title("⚾ MLB Analytics AI")
st.markdown("Ask me anything about MLB teams, players, and statistics!")

# Create a new agent session
def create_agent_session():
    try:
        url = f"{AGENT_URL}/apps/mlb_scout/users/student_13/sessions/{st.session_state.session_id}"
        # Get a fresh session from our agent
        response = requests.post(url, json={"state": {}}, timeout=60)
        if response.status_code == 200:
            st.session_state.session_created = True
            st.sidebar.success("Agent session created")
        else:
            st.sidebar.error(f"Failed to create session: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"Error creating session: {e}")

if not st.session_state.session_created:
    create_agent_session()

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# === Response parser ===
def parse_agent_response(result, verbose=False):
    """Parse full agent response and extract assistant text + sidebar logs."""
    full_response = ""

    for idx, item in enumerate(result):
        content = item.get("content", {})
        parts = content.get("parts", [])

        st.sidebar.markdown(f"---\n**🔹 Step {idx + 1}**")

        for part in parts:
            if "text" in part:
                text = part["text"]
                full_response += text + "\n\n"
                st.sidebar.markdown("🗣️ **Assistant said:**")
                st.sidebar.markdown(text)
            elif verbose and "functionCall" in part:
                st.sidebar.markdown("🔧 **Function Call:**")
                st.sidebar.code(json.dumps(part["functionCall"], indent=2))
            elif verbose and "functionResponse" in part:
                st.sidebar.markdown("📬 **Function Response:**")
                st.sidebar.code(json.dumps(part["functionResponse"], indent=2))

    return full_response.strip() or "*No assistant text returned.*"

# === Main Chat Input Handling ===
if prompt := st.chat_input("What would you like to know about MLB?"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Send user ID, session, and prompt to agent
                response = requests.post(
                    f"{AGENT_URL}/run",
                    json={
                        "app_name": "mlb_scout",
                        "user_id": "student_13",
                        "session_id": st.session_state.session_id,
                        "new_message": {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    },
                    timeout=300
                )

                if response.status_code == 200:
                    result = response.json()
                    
                    if show_raw_json:
                        st.sidebar.markdown("### 📦 Full Response JSON")
                        st.sidebar.json(result)

                    if isinstance(result, list) and result:
                        parsed = parse_agent_response(result, verbose=verbose_mode)
                        st.markdown(parsed)
                        st.session_state.messages.append({"role": "assistant", "content": parsed})
                    else:
                        st.error("Unexpected response format from the agent.")
                else:
                    st.error(f"Error: {response.status_code} from agent.")

            except Exception as e:
                st.error(f"Error communicating with the agent: {e}")

# Footer
st.markdown("---")
st.markdown("*Powered by Google Cloud ADK and Gemini*")
