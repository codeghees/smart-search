import os
from firecrawl.firecrawl import FirecrawlApp
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        load_dotenv()
        self.firecrawl = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
        # Create markdown directory if it doesn't exist
        self.markdown_dir = Path('markdown')
        self.markdown_dir.mkdir(exist_ok=True)

    def scrape_url(self, url):
        """Scrape content from a URL using Firecrawl API"""
        try:
            result = self.firecrawl.scrape_url(url, params={'formats': ['markdown']})
            domain = urlparse(url).netloc
            
            # Save markdown to file
            markdown_path = self.markdown_dir / f"{domain}.md"
            markdown_path.write_text(result['markdown'])
            
            return {
                'url': url,
                'domain': domain,
                'content': result['markdown'],
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'content': '',
                'status': 'error',
                'error': str(e)
            }