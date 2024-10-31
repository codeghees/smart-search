import anthropic
from typing import List, Dict
from serp_search import search as serp_search
from scraper import WebScraper
import os
import logging
from pathlib import Path
import json
from datetime import datetime


scraper = WebScraper()

# Create interactions directory if it doesn't exist
interactions_dir = Path('interactions')
interactions_dir.mkdir(exist_ok=True)

def log_claude_interaction(prompt, response, interaction_type=""):
    """Log Claude interactions to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = interactions_dir / f"claude_interaction_{timestamp}_{interaction_type}.json"
    
    interaction = {
        "timestamp": timestamp,
        "type": interaction_type,
        "input": prompt,
        "output": response
    }
    
    with open(filename, 'w') as f:
        json.dump(interaction, f, indent=2)

def process_tool_call(tool_name, tool_input):
    """Process tool calls and return results"""
    if tool_name == "get_content":
        logging.info(f"Getting content for {tool_input['url']}")
        return get_content(tool_input["url"])
    elif tool_name == "search":
        logging.info(f"Searching for {tool_input['query']}")
        return search(tool_input["query"])

def get_content(url):
    """
    Get the content of a webpage in Markdown format.
    """
    return scraper.scrape_url(url)['content']

def search(query):
    """
    Perform a Google search using the SerpAPI.
    """
    results = serp_search(query)
    return ','.join(result['link'] for result in results)

class ContentAnalyzer:
    def __init__(self, claude_client: anthropic.Anthropic):
        self.claude = claude_client

    def analyze_single_page(self, content: Dict) -> str:
        """Analyze content from a single webpage"""
        if content['status'] == 'error':
            return f"Error analyzing {content['url']}: {content['error']}"
            
        prompt = f"""Analyze the following webpage content from {content['url']}:

{content['content'][:10000]}  # Limiting content length

Please provide a detailed analysis that will be used as input for a comprehensive multi-source summary later:

1. A thorough summary capturing all major points (this will be compared with other sources)
2. Key facts, statistics, and evidence presented
3. Main arguments or positions taken
4. Methodology or approach used (if applicable) 
5. Credibility indicators (author expertise, citations, data sources)
6. Unique perspectives or insights not commonly found elsewhere
7. Any limitations, caveats or potential biases
8. Areas where this source excels or provides unique value
9. How this information relates to the broader topic

Format your response in Markdown, ensuring all key details are preserved for cross-source analysis."""

        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        log_claude_interaction(prompt, response.content[0].text, "single_page_analysis")
        return response.content[0].text

    def _get_intermediate_analysis(self, summaries: List[str], original_query: str, raw_results: str, 
                                 iteration: int, num_iterations: int, previous_analysis: str = "") -> str:
        """Get intermediate analysis for a single iteration"""
        prompt = f"""Analyze these webpage contents for the search query "{original_query}":

Raw Results JSON: {raw_results}

{''.join(summaries)}

Previous Analysis: {previous_analysis}

This is iteration {iteration + 1} of {num_iterations}. As an intelligent research assistant, analyze the available information and:

1. Key Areas for Investigation:
   - List specific points that require deeper research
   - Identify claims that need fact-checking
   - Note any contradictions between sources

2. Source Connections & Patterns:
   - Highlight relationships between different sources
   - Map how information flows and builds across sources
   - Identify consensus views vs outlier perspectives

3. Knowledge Gaps:
   - Outline missing context or background information
   - Note unanswered questions from the current sources
   - Identify areas where expert input would be valuable

4. Working Hypotheses:
   - Propose evidence-based explanations for observations
   - Suggest potential cause-effect relationships
   - Frame testable predictions based on available data

Available Research Tools:
- get_content(url: str): Retrieves webpage content in Markdown format
- search(query: str): Performs a Google search, returns relevant URLs

Current Context:
- Initial data comes from Google search results and scraped webpage content
- You can actively investigate by:
  * Diving deeper into specific URLs using get_content()
  * Expanding the search with new queries using search()
  * Following leads across multiple sources
  * Clarifying ambiguous terms or concepts with focused searches
  * IF you use a tool, that does not count in your iteration count! Use it.
  * If previous analysis asks for tool (search or get_content), you must use it.

Focus on building a clear understanding of the topic through methodical analysis. Document your reasoning and next steps for investigation. This is an intermediate analysis to guide further research."""

        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
            tools=[
                {
                    "name": "get_content",
                    "description": "Get the content of a webpage in Markdown format",
                    "input_schema": {
                        "type": "object", 
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL of the webpage to scrape"
                            }
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "search", 
                    "description": "Perform a Google search using the SerpAPI",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query string"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        )

        print(f"Stop Reason: {response.stop_reason}")

        if response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input

            print(f"\nTool Used: {tool_name}")
            print(f"Tool Input: {tool_input}")

            tool_result = process_tool_call(tool_name, tool_input)
            print(f"Tool Result: {tool_result}")

            final_response = self.claude.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": tool_result,
                            }
                        ],
                    },
                ],
                tools=[
                    {
                        "name": "get_content",
                        "description": "Get the content of a webpage in Markdown format",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"}
                            },
                            "required": ["url"]
                        }
                    },
                    {
                        "name": "search",
                        "description": "Perform a Google search using the SerpAPI",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    }
                ]
            )
        else:
            final_response = response

        final_text = next(
            (block.text for block in final_response.content if hasattr(block, "text")),
            None,
        )
        
        log_claude_interaction(prompt, final_text, f"intermediate_analysis_{iteration}")
        return final_text

    def _get_final_analysis(self, summaries: List[str], original_query: str, raw_results: str, 
                           previous_analysis: str) -> str:
        """Get final analysis after intermediate iterations"""
        prompt = f"""Analyze these webpage contents for the search query "{original_query}":

Raw Results JSON: {raw_results}

{''.join(summaries)}

Previous Analysis: {previous_analysis}

Write a crisp, focused FINAL summary that:
1. Synthesizes key information from all sources
2. Highlights important data points and facts
3. Notes any major differences between sources
4. Identifies the most credible information

Keep the response concise and factual. Format in Markdown."""

        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        log_claude_interaction(prompt, response.content[0].text, "final_analysis")
        return response.content[0].text

    def analyze_multiple_pages(self, contents: List[Dict], original_query: str, raw_results: str, num_iterations: int = 5) -> str:
        """Analyze and compare content from multiple webpages using iterative chain of thought"""
        # If num_iterations is 1, use original prompt
        if num_iterations == 1:
            summaries = []
            for content in contents:
                if content['status'] == 'success':
                    summaries.append(f"Content from {content['url']}:\n{content['content'][:5000]}")

            prompt = f"""Analyze these webpage contents for the search query "{original_query}":

Raw Results JSON: {raw_results}

{''.join(summaries)}

Write a crisp, focused summary that:
1. Synthesizes key information from all sources
2. Highlights important data points and facts
3. Notes any major differences between sources
4. Identifies the most credible information

Keep the response concise and factual. Format in Markdown."""

            response = self.claude.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            log_claude_interaction(prompt, response.content[0].text, "single_iteration_analysis")
            return response.content[0].text

        # For multiple iterations, use chain of thought
        summaries = []
        for content in contents:
            if content['status'] == 'success':
                summaries.append(f"Content from {content['url']}:\n{content['content'][:5000]}")

        current_analysis = ""
        # Get intermediate analyses
        for iteration in range(num_iterations - 1):
            print(f"\nIteration {iteration + 1} of {num_iterations}")
            current_analysis = self._get_intermediate_analysis(
                summaries, original_query, raw_results, iteration, num_iterations, current_analysis
            )

        # Get final analysis
        return self._get_final_analysis(summaries, original_query, raw_results, current_analysis)