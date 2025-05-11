# tframex_config.py
import os
import logging
from dotenv import load_dotenv
import aiohttp # For async HTTP requests

from tframex import (
    TFrameXApp, OpenAIChatLLM
    # Message # Not strictly needed if the tool just returns a string of titles
)

# --- Environment and Logging Setup ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s'
)
logging.getLogger("tframex").setLevel(logging.INFO)

# --- LLM Configuration ---
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama")
)

if not default_llm_config.api_base_url:
    raise ValueError("Error: OPENAI_API_BASE not set for default LLM configuration.")
if not default_llm_config.api_key:
    raise ValueError("Error: OPENAI_API_KEY not set for default LLM configuration.")

# --- Initialize TFrameX Application ---
tframex_app = TFrameXApp(default_llm=default_llm_config)


# --- Tool Definitions ---

@tframex_app.tool(description="Retrieves the titles of the top (up to 10) hot posts from a given Reddit community. Requires 'community_name'.")
async def get_reddit_top_post_titles(community_name: str, limit: int = 10) -> str:
    """Fetches the titles of the top N hot posts from a subreddit."""
    logging.info(f"TOOL EXECUTED: get_reddit_top_post_titles(community_name='{community_name}', limit={limit})")
    if not community_name:
        return "Error: Please provide a Reddit community name (subreddit)."
    if not 1 <= limit <= 25: # Reddit API usually has a max of 100, but 25 is reasonable for this use.
        logging.warning(f"get_reddit_top_post_titles: Invalid limit '{limit}'. Clamping to 10.")
        limit = 10 # Sensible default if invalid

    if community_name.lower().startswith("r/"):
        community_name = community_name[2:]

    url = f"https://www.reddit.com/r/{community_name}/hot/.json?limit={limit}"
    headers = {'User-Agent': 'TFrameX Reddit Titles Tool v0.1 (ExampleApp)'} 

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    logging.warning(f"get_reddit_top_post_titles: Subreddit r/{community_name} not found. Status: {response.status}")
                    return f"Error: Could not find the subreddit r/{community_name}. It might be private, banned, or non-existent."
                if response.status == 403:
                     logging.warning(f"get_reddit_top_post_titles: Access forbidden to r/{community_name}. Status: {response.status}")
                     return f"Error: Access to r/{community_name} is forbidden. It might be a private community."
                response.raise_for_status() # For other errors like 5xx or 429
                data = await response.json()

        titles = [
            post['data']['title']
            for post in data.get('data', {}).get('children', [])
            if post.get('kind') == 't3' and 'data' in post and 'title' in post['data'] and post['data']['title']
        ]

        if not titles:
            logging.info(f"get_reddit_top_post_titles: No posts found in r/{community_name}.")
            return f"No posts found in r/{community_name}, or titles could not be extracted. The community might be empty or have no recent posts with titles."

        titles_str = f"Top {len(titles)} post titles from r/{community_name}:\n" + "\n".join([f"- {title}" for title in titles])
        logging.info(f"get_reddit_top_post_titles: Successfully retrieved {len(titles)} titles for r/{community_name}.")
        return titles_str

    except aiohttp.ClientConnectorError as e:
        logging.error(f"get_reddit_top_post_titles: Network error for r/{community_name}: {e}")
        return f"Error: Could not connect to Reddit to fetch titles for r/{community_name}."
    except aiohttp.ClientResponseError as e:
        logging.error(f"get_reddit_top_post_titles: HTTP error for r/{community_name}. Status: {e.status}, Message: {e.message}")
        if e.status == 429: # Too Many Requests
            return f"Error: Requests to Reddit are temporarily rate-limited for r/{community_name}. Please try again later."
        return f"Error: API error fetching titles for r/{community_name} (HTTP {e.status})."
    except Exception as e:
        logging.exception(f"get_reddit_top_post_titles: An unexpected error occurred for r/{community_name}")
        return f"Error: An unexpected error occurred while fetching titles for r/{community_name}."


# --- Agent Definition ---

@tframex_app.agent(
    name="RedditAnalystAgent",
    description="Analyzes the current topics and sentiment of a Reddit community based on its top post titles.",
    system_prompt=(
        "You are a Reddit Analyst. Your goal is to understand what's currently being discussed and the general sentiment in a given subreddit. "
        "You have a tool called 'get_reddit_top_post_titles' that provides you with a list of recent post titles from a community.\n"
        "{available_tools_descriptions}\n\n" # TFrameX will populate this
        "When a user asks about a subreddit (e.g., 'What's happening in r/LocalLLaMA?' or 'What's the vibe in r/python?'):\n"
        "1. Use the 'get_reddit_top_post_titles' tool to fetch the titles for the specified 'community_name'.\n"
        "2. Once you receive the list of titles from the tool, analyze them to determine the main topics of discussion and the overall sentiment (e.g., positive, negative, neutral, excited, concerned, mixed, etc.).\n"
        "3. Provide a concise summary (2-3 sentences) of your analysis. If the tool returns an error or no titles, report that problem clearly.\n"
        "Example user query: 'What's up with r/futurology?'\n"
        "Example your thought process after getting titles: 'Okay, I have the titles. Looks like there's a lot of talk about AI ethics and space exploration. Sentiment seems cautiously optimistic.'\n"
        "Example your response to user: 'In r/futurology, recent discussions seem to focus on AI ethics and new space exploration initiatives. The general sentiment appears to be one of cautious optimism and active debate.'\n"
        "Be direct and informative in your analysis."
    ),
    tools=["get_reddit_top_post_titles"],
    strip_think_tags=True
)
async def reddit_analyst_agent_placeholder():
    pass

logging.info("TFrameX application, Reddit tool, and RedditAnalystAgent configured.")
logging.info("Reminder: This script requires 'aiohttp'. Install with 'pip install aiohttp'.")

# To make the app instance easily importable by flask_app.py
def get_tframex_app():
    return tframex_app