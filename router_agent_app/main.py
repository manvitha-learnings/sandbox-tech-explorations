import os
import re
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize Gemini client
client = genai.Client()
MODEL_NAME = "gemini-3.5-flash"

# --- Step 1: Agent System Prompts ---
ROUTER_PROMPT = """
You are a classification router. Analyze the user request and output EXACTLY one route key from this list:
- 'foodie_agent': Query asks ONLY about food or restaurant recommendations.
- 'weekend_guide_agent': Query asks about local events/concerts.
- 'find_and_navigate_combo': Query requires finding a venue AND getting directions to it.

Return ONLY the key name. No markdown, no explanations.
"""

FOODIE_PROMPT = """
You are an expert culinary critic. Recommend the top venue for the user's request.
CRITICAL: Always put the restaurant name in double asterisks, e.g., **Jin Sho**, so the system can parse it.
"""

NAV_PROMPT = """
You are a transit specialist. Provide concise directions from a starting point to a destination.
"""

# --- Step 2: Agent Runner Helpers ---
async def run_agent(prompt: str, user_input: str) -> str:
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL_NAME,
        contents=f"{prompt}\n\nUser Query: {user_input}"
    )
    return response.text.strip()

def extract_venue(text: str) -> str:
    match = re.search(r'\*\*(.*?)\*\*', text)
    return match.group(1).strip() if match else "the venue"

# --- Step 3: Sequential Routing Orchestrator ---
async def process_query(user_query: str):
    print(f"\n{'='*50}\nIncoming Query: '{user_query}'")
    
    # 1. Router Agent Decides
    route = await run_agent(ROUTER_PROMPT, user_query)
    clean_route = route.replace("'", "").replace('"', '').strip()
    print(f"🚦 Selected Route: {clean_route}")

    # 2. Sequential Chain Execution
    if clean_route == "find_and_navigate_combo":
        print("\n[Step 1] Running Foodie Agent...")
        food_result = await run_agent(FOODIE_PROMPT, user_query)
        print(f"Foodie Agent Output:\n{food_result}\n")

        destination = extract_venue(food_result)
        print(f"💡 Extracted Destination: {destination}")

        print("\n[Step 2] Passing context to Transportation Agent...")
        nav_query = f"Give directions to {destination} from the nearest major train station."
        nav_result = await run_agent(NAV_PROMPT, nav_query)
        print(f"Transportation Agent Output:\n{nav_result}")

    elif clean_route == "foodie_agent":
        result = await run_agent(FOODIE_PROMPT, user_query)
        print(f"Result:\n{result}")

    else:
        print(f"Route '{clean_route}' executed directly.")

# --- Step 4: Run Test Queries ---
async def main():
    queries = [
        "I want the best sushi in Palo Alto.",
        "Find me the best sushi in Palo Alto and show me how to get there from Caltrain."
    ]
    for q in queries:
        await process_query(q)

if __name__ == "__main__":
    asyncio.run(main())