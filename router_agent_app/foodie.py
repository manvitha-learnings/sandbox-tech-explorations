from pydantic import BaseModel, Field

class FoodieRecommendation(BaseModel):
    venue_name: str = Field(description="The exact name of the recommended restaurant.")
    cuisine: str = Field(description="Type of food served.")
    summary_review: str = Field(description="Brief explanation of why this place was recommended.")

FOODIE_PROMPT = "You are an expert culinary critic. Recommend the absolute best venue for the user's request."