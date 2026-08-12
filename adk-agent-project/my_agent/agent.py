import os
from google.adk.agents import Agent
from dotenv import load_dotenv

load_dotenv()

# Define your sub-agents
foodie_agent = Agent(
    name="foodie_agent",
    model="gemini-2.5-flash",
    instruction="You are an expert food critic."
)

transportation_agent = Agent(
    name="transportation_agent",
    model="gemini-2.5-flash",
    instruction="You are a transit specialist."
)

# Root Router Agent
root_agent = Agent(
    name="router_agent",
    model="gemini-2.5-flash",
    instruction="Route requests to sub-agents.",
    sub_agents=[foodie_agent, transportation_agent]
)