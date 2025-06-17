from google.adk.agents import Agent
from google.adk.tools import google_search  # Import the tool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

root_agent = Agent(
   # A unique name for the agent.
   name="basic_search_agent",
   # The Large Language Model (LLM) that agent will use.
   model="gemini-2.0-flash-exp",
   # model="gemini-2.0-flash-live-001",  # New streaming model version as of Feb 2025
   # A short description of the agent's purpose.
   description="Agent to answer questions using Google Search."
                "You also have the capability to do image analysis wherein the user will provide you with the link to the image."
                "Using the link you must analyze the image that has been uploaded by the user.",
   # Instructions to set the agent's behavior.
   instruction="You are an expert researcher. You always stick to the facts.",
   # Add google_search tool to perform grounding with Google search.
   tools=[google_search]
)

# --- NEW ADDITIONS TO FIX CORS START HERE ---

# 1. Create a FastAPI application instance.
# The 'adk api_server' command will look for this 'app' object at the top level.
app = FastAPI()

# 2. Configure CORS middleware for the FastAPI app.
origins = [
    "http://localhost:3000",  # Your React app's development server URL
    "http://127.0.0.1:3000",  # Sometimes React might use this loopback address
    # Add any other origins where your frontend might be hosted in the future:
    # "https://your-production-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)