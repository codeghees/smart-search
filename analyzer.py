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

    def _get_intermediate_analysis(self, summaries: List[str], original_query: str, raw_results: str, 
                                 iteration: int, num_iterations: int, previous_analysis: str = "") -> str:
        """Get intermediate analysis for a single iteration"""
        prompt = f"""Analyze these webpage contents for the search query "{original_query}":

Raw Results JSON: {raw_results}

{''.join(summaries)}

Previous Analysis: {previous_analysis}

This is iteration {iteration + 1} of {num_iterations}. Write intermediate analysis that:
1. Lists key points that need further investigation
2. Notes potential connections between sources that need verification
3. Identifies gaps in understanding that need clarification
4. Proposes hypotheses about the topic that need testing

Use this as a scratch pad to develop your understanding. The final synthesis will come later."""

        response = self.claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

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
        return response.content[0].text

    def analyze_multiple_pages(self, contents: List[Dict], original_query: str, raw_results: str, num_iterations: int = 3) -> str:
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
            return response.content[0].text

        # For multiple iterations, use chain of thought
        summaries = []
        for content in contents:
            if content['status'] == 'success':
                summaries.append(f"Content from {content['url']}:\n{content['content'][:5000]}")

        current_analysis = ""
        # Get intermediate analyses
        for iteration in range(num_iterations - 1):
            current_analysis = self._get_intermediate_analysis(
                summaries, original_query, raw_results, iteration, num_iterations, current_analysis
            )

        # Get final analysis
        return self._get_final_analysis(summaries, original_query, raw_results, current_analysis)