import os, asyncio, time, logging, streamlit as st
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from dotenv import load_dotenv

load_dotenv(); logging.basicConfig(level=logging.ERROR)
MODEL,APP_NAME,USER_ID = "gemini-2.0-flash-exp", "search_assistant_app", "streamlit_user_search"
agent = Agent(name="search_assistant", model=MODEL, instruction="You are a helpful assistant Answer user questions using Google Search when needed.", description="An assistant that can search the web.", tools=[google_search])

@st.cache_resource
def init_adk():
    ss = InMemorySessionService(); r = Runner(agent=agent, app_name=APP_NAME, session_service=ss)
    sid = st.session_state.get("adk_session_id") or f"session_{int(time.time())}_{os.urandom(4).hex()}"; st.session_state["adk_session_id"] = sid
    try: ss.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sid, state={})
    except: ss.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=sid, state={})
    return r, sid

async def run_adk(r, sid, q):
    try:
        async for e in r.run_async(user_id=USER_ID, session_id=sid, new_message=types.Content(role="user", parts=[types.Part(text=q)])):
            if e.is_final_response() and e.content and e.content.parts: return e.content.parts[0].text
    except Exception as err: return f"Error: {err}"
    return "[No response]"

def main():
    st.set_page_config(page_title="Search", page_icon="🔍", layout="wide"); 
    st.markdown(
    f'<h1><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/1200px-Google_2015_logo.svg.png" width="135"/> Agent Development Kit <img src="https://cdn-images-1.medium.com/v2/resize:fill:1600:480/gravity:fp:0.5:0.4/1*A4-k_sI5kmrphjS4tJ_rpA.png" width="70"/><img src="https://images.seeklogo.com/logo-png/44/2/streamlit-logo-png_seeklogo-441815.png" width="60"/></h1>',
    unsafe_allow_html=True
    )
    if not os.environ.get("GOOGLE_API_KEY"): st.error("API Key missing!"); st.stop()
    try: r, sid = init_adk(); # st.sidebar.success(f"ADK Connected (Session: ...{sid[-8:]})", icon="✅")
    except Exception as e: st.error(f"ADK failed: {e}", icon="❌"); st.stop()
    if "msgs" not in st.session_state: st.session_state.msgs = []
    for msg in st.session_state.msgs:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("Ask..."):
        st.session_state.msgs.append({"role": "user", "content": prompt}); 
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("Searching..."): response = asyncio.run(run_adk(r, sid, prompt)); placeholder.markdown(response)
        st.session_state.msgs.append({"role": "assistant", "content": response})
    st.sidebar.image("https://cdn-images-1.medium.com/v2/resize:fill:1600:480/gravity:fp:0.5:0.4/1*A4-k_sI5kmrphjS4tJ_rpA.png", use_container_width=True)
    st.sidebar.caption(f"**Model**: **{MODEL}**")

if __name__ == "__main__": main()