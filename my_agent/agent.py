from google.adk.agents import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
load_dotenv()

root_agent = Agent(
    name="search_assistant",
    model="gemini-2.0-flash-exp", 
    instruction="You are a helpful assistant. " \
    "Answer user questions using Google Search when needed.",
    description="An assistant that can search the web.",
    tools=[google_search]
)
