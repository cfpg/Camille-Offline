from tools import register_tool
import requests
import os
from config import Config


SETUP_INSTRUCTIONS = """
1. Visit https://brave.com/search/api/
2. Sign up for a free or paid Brave Search API subscription
3. Create a new API key in your dashboard
4. Copy your API key to .env file as: BRAVE_SEARCH_API_TOKEN="your-key-here"
"""

def _get_setup_message(reason: str) -> str:
    return (
        "IMPORTANT: Do not provide information from your knowledge base. "
        f"I cannot search the web because {reason}. "
        "You must respond to the user with this message:\n\n"
        "I apologize, but I cannot search the web for this information right now. "
        "To enable web searching capabilities, you'll need to set up Brave Search first. "
        "Here are the steps:\n"
        f"{SETUP_INSTRUCTIONS}\n"
        "Once you've completed these steps, I'll be able to search the web and provide you with accurate, up-to-date information."
    )

@register_tool
def brave_search(query: str) -> str:
    """
    Search the web using Brave Search API and return relevant results.
    
    Args:
        query: The search query string
    
    Returns:
        Summary of search results or error message
    """
    if not Config.BRAVE_SEARCH_API_TOKEN:
        return _get_setup_message("Brave Search is not yet configured on this system")

    try:
        headers = {
            "X-Subscription-Token": Config.BRAVE_SEARCH_API_TOKEN,
            "Accept": "application/json",
        }
        
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {
            "q": query,
            "count": 5,
            "text_decorations": False,
            "text_snippets": True
        }
        
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 401:
            return _get_setup_message("the Brave Search API token is invalid")
        
        response.raise_for_status()
        data = response.json()
        
        if not data.get("web", {}).get("results"):
            return f"No results found for: {query}"
            
        results = data["web"]["results"]
        
        summary = []
        for result in results:
            summary.append(f"- {result['title']}: {result['description']}")
            
        return "\n\n".join(summary)

    except requests.exceptions.RequestException as e:
        if "401" in str(e):
            return _get_setup_message("the Brave Search API token is invalid")
        return f"Error performing search: {str(e)}"
