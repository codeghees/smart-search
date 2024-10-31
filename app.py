import streamlit as st
import anthropic
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import json
from scraper import WebScraper
from analyzer import ContentAnalyzer

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
    # print(f"Raw Results JSON: {json.dumps(results, indent=2)}")
    return results.get('organic_results', []), json.dumps(results, indent=2)

def process_search_results(query, results, raw_results):
    """Process search results including web scraping and analysis"""
    scraper = WebScraper()
    analyzer = ContentAnalyzer(claude)
    
    # Scrape content from each URL
    scraped_contents = []
    analyzed_contents = []
    with st.spinner("Scraping webpage contents..."):
        for result in results:
            content = scraper.scrape_url(result['link'])
            scraped_contents.append(content)
            
    # Analyze individual pages
    
    for content in scraped_contents:
        if content['status'] == 'success':
            with st.expander(f"Analysis: {content['domain']}"):
                analysis = analyzer.analyze_single_page(content)
                analyzed_contents.append({
                    'url': content['url'],
                    'domain': content['domain'],
                    'content': analysis,
                    'status': 'success'
                })
                # st.markdown(analysis)
                
    # Comprehensive analysis across all pages
    st.subheader("Comprehensive Analysis")
    comprehensive_analysis = analyzer.analyze_multiple_pages(analyzed_contents, query, raw_results)
    st.markdown(comprehensive_analysis)

    st.subheader("Individual Page Analyses")
    for content in analyzed_contents:
        with st.expander(f"**{content['domain']}**"):
            st.markdown(content['content'])


# App title and description
st.title("🔍 Smart Search Engine")
st.markdown("""
This search engine combines a search API for web results with Claude's analysis capabilities
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
            
            # Process and analyze results
            process_search_results(query, results, raw_results)
            
            # Search Results Links
            # st.markdown("---")
            # st.subheader("Search Results")
            # for result in results:
            #     st.markdown(f"[{result['title']}]({result['link']})")
            #     st.markdown(f"> {result['snippet']}")
            #     st.markdown("---")
    else:
        st.warning("Please enter a search query")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, SERP API, and Claude")