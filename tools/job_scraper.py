"""
Job Web Scraper
Automatically fetch job descriptions from job posting URLs.
Supports: LinkedIn, Indeed, Greenhouse, Lever, and general websites.
"""
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class JobScraper:
    """
    Scrape job postings from various platforms.

    Supported platforms:
    - LinkedIn Jobs
    - Indeed
    - Greenhouse
    - Lever
    - Generic websites
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape_job(self, url: str) -> Dict[str, Any]:
        """
        Scrape job posting from URL.

        Args:
            url: Job posting URL

        Returns:
            Dictionary with job_description, company, role, and metadata
        """
        try:
            # Determine platform
            domain = urlparse(url).netloc.lower()

            if 'linkedin.com' in domain:
                return self._scrape_linkedin(url)
            elif 'indeed.com' in domain:
                return self._scrape_indeed(url)
            elif 'greenhouse.io' in domain or 'boards.greenhouse.io' in domain:
                return self._scrape_greenhouse(url)
            elif 'lever.co' in domain or 'jobs.lever.co' in domain:
                return self._scrape_lever(url)
            else:
                return self._scrape_generic(url)

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'job_description': None,
                'company': None,
                'role': None
            }

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse webpage."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _scrape_linkedin(self, url: str) -> Dict[str, Any]:
        """Scrape LinkedIn job posting."""
        soup = self._fetch_page(url)
        if not soup:
            return self._error_response("Failed to fetch LinkedIn page")

        # Extract job description
        description_div = soup.find('div', {'class': 'show-more-less-html__markup'})
        if not description_div:
            description_div = soup.find('div', {'class': 'description'})

        job_description = description_div.get_text(strip=True, separator='\n') if description_div else None

        # Extract company name
        company_tag = soup.find('a', {'class': 'topcard__org-name-link'})
        if not company_tag:
            company_tag = soup.find('span', {'class': 'topcard__flavor'})
        company = company_tag.get_text(strip=True) if company_tag else None

        # Extract role/title
        title_tag = soup.find('h1', {'class': 'topcard__title'})
        if not title_tag:
            title_tag = soup.find('h1')
        role = title_tag.get_text(strip=True) if title_tag else None

        return {
            'success': True,
            'job_description': job_description,
            'company': company,
            'role': role,
            'platform': 'LinkedIn',
            'url': url
        }

    def _scrape_indeed(self, url: str) -> Dict[str, Any]:
        """Scrape Indeed job posting."""
        soup = self._fetch_page(url)
        if not soup:
            return self._error_response("Failed to fetch Indeed page")

        # Extract job description
        description_div = soup.find('div', {'id': 'jobDescriptionText'})
        if not description_div:
            description_div = soup.find('div', {'class': 'jobsearch-jobDescriptionText'})

        job_description = description_div.get_text(strip=True, separator='\n') if description_div else None

        # Extract company
        company_tag = soup.find('div', {'class': 'jobsearch-InlineCompanyRating'})
        if not company_tag:
            company_tag = soup.find('div', {'class': 'icl-u-lg-mr--sm'})
        company = company_tag.get_text(strip=True) if company_tag else None

        # Extract title
        title_tag = soup.find('h1', {'class': 'jobsearch-JobInfoHeader-title'})
        if not title_tag:
            title_tag = soup.find('h1')
        role = title_tag.get_text(strip=True) if title_tag else None

        return {
            'success': True,
            'job_description': job_description,
            'company': company,
            'role': role,
            'platform': 'Indeed',
            'url': url
        }

    def _scrape_greenhouse(self, url: str) -> Dict[str, Any]:
        """Scrape Greenhouse job posting."""
        soup = self._fetch_page(url)
        if not soup:
            return self._error_response("Failed to fetch Greenhouse page")

        # Extract job description
        description_div = soup.find('div', {'id': 'content'})
        if not description_div:
            description_div = soup.find('div', {'class': 'content'})

        job_description = description_div.get_text(strip=True, separator='\n') if description_div else None

        # Extract company from URL or header
        company = None
        company_link = soup.find('a', {'id': 'header'})
        if company_link:
            company = company_link.get_text(strip=True)
        else:
            # Extract from URL (e.g., boards.greenhouse.io/company/...)
            match = re.search(r'greenhouse\.io/([^/]+)', url)
            if match:
                company = match.group(1).replace('-', ' ').title()

        # Extract title
        title_tag = soup.find('h1', {'class': 'app-title'})
        if not title_tag:
            title_tag = soup.find('h1')
        role = title_tag.get_text(strip=True) if title_tag else None

        return {
            'success': True,
            'job_description': job_description,
            'company': company,
            'role': role,
            'platform': 'Greenhouse',
            'url': url
        }

    def _scrape_lever(self, url: str) -> Dict[str, Any]:
        """Scrape Lever job posting."""
        soup = self._fetch_page(url)
        if not soup:
            return self._error_response("Failed to fetch Lever page")

        # Extract job description
        description_div = soup.find('div', {'class': 'content'})
        if not description_div:
            description_div = soup.find('div', {'class': 'section-wrapper'})

        job_description = description_div.get_text(strip=True, separator='\n') if description_div else None

        # Extract company from URL
        match = re.search(r'jobs\.lever\.co/([^/]+)', url)
        company = match.group(1).replace('-', ' ').title() if match else None

        # Extract title
        title_tag = soup.find('h2', {'class': 'posting-headline'})
        if not title_tag:
            title_tag = soup.find('h1')
        role = title_tag.get_text(strip=True) if title_tag else None

        return {
            'success': True,
            'job_description': job_description,
            'company': company,
            'role': role,
            'platform': 'Lever',
            'url': url
        }

    def _scrape_generic(self, url: str) -> Dict[str, Any]:
        """Scrape generic job posting (fallback)."""
        soup = self._fetch_page(url)
        if not soup:
            return self._error_response("Failed to fetch page")

        # Try to find main content
        # Look for common job description containers
        description = None
        for selector in [
            {'class': re.compile(r'job.*description', re.I)},
            {'class': re.compile(r'description', re.I)},
            {'id': re.compile(r'job.*description', re.I)},
            {'class': re.compile(r'content', re.I)},
            {'role': 'main'},
            {'id': 'content'}
        ]:
            element = soup.find('div', selector)
            if element:
                description = element.get_text(strip=True, separator='\n')
                break

        # If still nothing, get main content
        if not description:
            main = soup.find('main') or soup.find('article') or soup.find('body')
            description = main.get_text(strip=True, separator='\n') if main else None

        # Extract title
        title_tag = soup.find('h1')
        role = title_tag.get_text(strip=True) if title_tag else None

        # Extract company from domain or title
        domain = urlparse(url).netloc.replace('www.', '').replace('.com', '').replace('.io', '')
        company = domain.title()

        return {
            'success': True,
            'job_description': description,
            'company': company,
            'role': role,
            'platform': 'Generic',
            'url': url
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            'success': False,
            'error': message,
            'job_description': None,
            'company': None,
            'role': None
        }


# CLI for testing
if __name__ == "__main__":
    scraper = JobScraper()

    # Test URLs
    test_urls = [
        "https://boards.greenhouse.io/anthropic/jobs/4305317008",
        # Add more test URLs as needed
    ]

    for url in test_urls:
        print(f"\nScraping: {url}")
        result = scraper.scrape_job(url)

        if result['success']:
            print(f"✓ Success!")
            print(f"  Company: {result.get('company', 'N/A')}")
            print(f"  Role: {result.get('role', 'N/A')}")
            print(f"  Description length: {len(result.get('job_description', '') or '')}")
            print(f"  Platform: {result.get('platform', 'N/A')}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
