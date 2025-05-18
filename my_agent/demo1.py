import os
import asyncio
import time
import logging
import streamlit as st
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

MODEL = "gemini-2.0-flash-exp"
APP_NAME = "search_assistant_app"
USER_ID = "streamlit_user_search"

agent = Agent(
    name="search_assistant",
    model=MODEL,
    instruction="Helpful assistant using Google Search.",
    description="Assistant for web searches.",
    tools=[google_search],
)

@st.cache_resource
def init_adk():
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session_id = st.session_state.get("adk_session_id") or f"session_{int(time.time())}_{os.urandom(4).hex()}"
    st.session_state["adk_session_id"] = session_id
    try:
        session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id, state={})
    except Exception as e:
        logging.exception("Session error:")
        session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id, state={})
    return runner, session_id


async def run_adk(runner, session_id, query):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    try:
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                return event.content.parts[0].text
    except Exception as e:
        logging.exception("ADK error:")
        return f"Error: {e}"
    return "[No response]"


def main():
    st.set_page_config(page_title="Search Assistant", page_icon="🔍", layout="wide")
    st.title("🔍 Search Assistant")

    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("API Key missing! Add to .env file.")
        st.stop()

    try:
        runner, session_id = init_adk()
        st.sidebar.success(f"ADK Connected (Session ID: ...{session_id[-8:]})", icon="✅")
    except Exception as e:
        st.error(f"ADK init failed: {e}", icon="❌")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("Searching..."):
                response = asyncio.run(run_adk(runner, session_id, prompt))
                placeholder.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    st.sidebar.caption(f"Model: {MODEL}")


if __name__ == "__main__":
    main()