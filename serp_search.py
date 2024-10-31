from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()

def search(query, num_results=10):
    """
    Perform a Google search using the SerpAPI.
    
    Args:
        query (str): The search query string
        num_results (int, optional): Number of results to return. Defaults to 10.
        
    Returns:
        list: List of search result dictionaries. Each dictionary contains:
            - position (int): Result position in search
            - title (str): Title of the webpage
            - link (str): Direct URL to the webpage
            - redirect_link (str): Google redirect URL
            - displayed_link (str): Shortened URL shown in results
            - favicon (str): URL to site favicon
            - date (str): Publication date if available
            - snippet (str): Text preview of the webpage
            - snippet_highlighted_words (list): Search terms found in snippet
            - source (str): Domain name of result
    """
    search = GoogleSearch({
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "num": num_results
    })
    results = search.get_dict()
    return results.get('organic_results', [])
