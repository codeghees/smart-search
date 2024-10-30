import anthropic
from typing import List, Dict
import os

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
        return response.content[0].text

    def analyze_multiple_pages(self, contents: List[Dict], original_query: str, raw_results: str) -> str:
        """Analyze and compare content from multiple webpages"""
        summaries = []
        for content in contents:
            if content['status'] == 'success':
                summaries.append(f"Content from {content['url']}:\n{content['content'][:5000]}")

        prompt = f"""Analyze these webpage contents related to the search query "{original_query}":

Raw Results JSON (from SERP API for additional context): {raw_results} 

{''.join(summaries)}
These results are summaries of the content from the webpages. Lean heavily on this for your analysis.
Please provide:
1. A comprehensive summary of findings across all sources
2. Common themes or patterns
3. Any contradictions or differences between sources
4. Most reliable or authoritative information found
5. Recommendations for further research
6. Keep the response concise and informative. Don't use too many headers.

Format your response in Markdown with appropriate headers and lists."""

        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text