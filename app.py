import streamlit as st
import anthropic
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Smart Search Engine",
    page_icon="🔍",
    layout="wide"
)

# Initialize API clients
claude = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

def perform_search(query, num_results=5):
    """Perform search using SERP API"""
    search = GoogleSearch({
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "num": num_results
    })
    results = search.get_dict()
    print(f"Raw Results JSON: {json.dumps(results, indent=2)}")
    return results.get('organic_results', []), json.dumps(results, indent=2)

def analyze_results(query, results, raw_results):
    """Analyze search results using Claude"""
    prompt = f"""Here are the search results for the query "{query}":
    
Raw Results JSON: {raw_results}

Please analyze these results and provide:
1. A brief summary of the main findings
2. Key highlights or important points
3. Any relevant insights or patterns noticed
4. Use specific information from the provided JSON where relevant

Format your entire response in Markdown, using appropriate headers, lists, and emphasis where needed.
Keep the response concise and informative."""

    print(f"Sending to Claude - Query: {query}")
    print(f"Results being analyzed: {json.dumps(results, indent=2)}")

    response = claude.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f"Claude's response: {response.content}")
    return response.content[0].text

# App title and description
st.title("🔍 Smart Search Engine")
st.markdown("""
This search engine combines SERP API for web results with Claude's analysis capabilities
to provide intelligent insights about your search query.
""")

# Search input
query = st.text_input("Enter your search query")
num_results = st.slider("Number of results", min_value=3, max_value=10, value=5)

if st.button("Search"):
    if query:
        with st.spinner("Searching..."):
            # Perform search
            results, raw_results = perform_search(query, num_results)
            
            # AI Analysis
            st.subheader("AI Analysis")
            analysis = analyze_results(query, results, raw_results)
            st.markdown(analysis)
            
            # Search Results Links
            st.markdown("---")
            st.subheader("Search Results")
            for result in results:
                st.markdown(f"[{result['title']}]({result['link']})")
                st.markdown(f"> {result['snippet']}")
                st.markdown("---")
    else:
        st.warning("Please enter a search query")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, SERP API, and Claude")