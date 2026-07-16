import streamlit as st
import requests
import json

st.set_page_config(page_title="AI Memory Vault Dashboard", layout="wide")
st.title("🧠 Interactive AI Memory Vault")
st.subheader("Sprint 22: Graph-Driven Conversational Agent")

# Initialize persistent message history lists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Keep past chat messages sticky on screen reload cycles
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Capture the entry prompt action
if user_prompt := st.chat_input("Ask the Memory Vault orchestrator..."):
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        # Setup structural layout element layout slots
        status_box = st.empty()
        thought_box = st.empty()
        text_box = st.empty()
        
        accumulated_text = ""
        accumulated_thoughts = []
        
        backend_url = "/api/v1/agent/chat"
        req_payload = {"message": user_prompt, "department": "FINANCE"}
        
        try:
            # Open a persistent stream to catch real-time agent event updates
            with requests.post(backend_url, json=req_payload, stream=True) as response:
                if response.status_code != 200:
                    st.error(f"Backend returned status code: {response.status_code}")
                
                # Read chunks line by line as they arrive from the server
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    
                    # Clean the SSE formatting tag
                    if line.startswith("data: "):
                        raw_json = line[6:].strip()
                        if not raw_json:
                            continue
                        
                        try:
                            event_data = json.loads(raw_json)
                        except Exception:
                            continue
                            
                        # Handle error dictionaries sent by the backend
                        if "error" in event_data:
                            st.error(f"Backend Node Error: {event_data['error']}")
                            continue
                            
                        # 🦉 FIX: Force the event type to uppercase so casing mismatches are impossible!
                        event_type = str(event_data.get("event_type", "")).upper()
                        node_name = event_data.get("node_name", "Orchestrator")
                        content = event_data.get("content", "")
                        
                        # Render the output live based on the event type
                        if "THOUGHT" in event_type:
                            accumulated_thoughts.append(f"**[{node_name}]**: {content}")
                            with thought_box.expander("🛠️ View Agent Timeline", expanded=True):
                                st.markdown("\n\n".join(accumulated_thoughts))
                                
                        elif "TOKEN" in event_type:
                            accumulated_text += content
                            text_box.markdown(accumulated_text)
                            
                        elif "FINAL" in event_type:
                            status_box.empty()
                            if not accumulated_text:
                                text_box.markdown(content)
                                accumulated_text = content
                                
                            sources = event_data.get("metadata", {}).get("sources", [])
                            if sources:
                                st.caption(f"📚 **Verified Source Contexts:** {', '.join(sources)}")
                                
            st.session_state.messages.append({"role": "assistant", "content": accumulated_text})
            
        except Exception as err:
            st.error(f"UI Stream Exception: {str(err)}")