from pydantic import BaseModel, Field

class RouteSelection(BaseModel):
    selected_route: str = Field(
        description="Must be one of: 'foodie_agent', 'weekend_guide_agent', 'find_and_navigate_combo'."
    )

ROUTER_PROMPT = """
Analyze the user request and determine the best route:
- 'foodie_agent': Query asks ONLY about food or restaurant recommendations.
- 'weekend_guide_agent': Query asks about local events/concerts.
- 'find_and_navigate_combo': Query requires finding a venue AND getting directions to it.
"""