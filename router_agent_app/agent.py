import os
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()

# Define sub-agents
foodie_agent = Agent(
    name="foodie_agent",
    model="gemini-3.5-flash",
    instruction="You are an expert culinary critic."
)

transportation_agent = Agent(
    name="transportation_agent",
    model="gemini-3.5-flash",
    instruction="You are a transit specialist."
)

# Root agent that ADK loads
root_agent = Agent(
    name="router_agent",
    model="gemini-3.5-flash",
    instruction="Route queries to appropriate worker agents.",
    sub_agents=[foodie_agent, transportation_agent]
)