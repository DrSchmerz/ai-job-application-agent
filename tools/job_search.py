"""
Job Board Search - Search multiple job boards and aggregate results.
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class JobBoardSearch:
    """Search across multiple job boards."""

    def __init__(self):
        self.supported_boards = [
            "LinkedIn",
            "Wellfound (AngelList)",
            "Indeed",
            "Glassdoor",
            "Remote.co",
            "WeWorkRemotely"
        ]

    def build_search_urls(
        self,
        role: str,
        location: str = "Europe",
        remote: bool = True,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Build search URLs for multiple job boards.

        Args:
            role: Job title (e.g., "Sales Engineer")
            location: Location (e.g., "Europe", "Germany", "Remote")
            remote: Include remote jobs
            keywords: Additional keywords (e.g., ["SaaS", "B2B"])

        Returns:
            Dictionary of {board_name: search_url}
        """
        # Clean role for URL
        role_encoded = role.replace(" ", "%20")
        location_encoded = location.replace(" ", "%20")

        keyword_string = ""
        if keywords:
            keyword_string = "%20".join(keywords)

        urls = {}

        # LinkedIn
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={role_encoded}"
        if location != "Remote":
            linkedin_url += f"%20{location_encoded}"
        if remote:
            linkedin_url += "&f_WT=2"  # Remote filter
        urls["LinkedIn"] = linkedin_url

        # Wellfound (AngelList)
        wellfound_role = role.lower().replace(" ", "-")
        urls["Wellfound"] = f"https://wellfound.com/role/l/{wellfound_role}/europe"

        # Indeed
        indeed_url = f"https://www.indeed.com/jobs?q={role_encoded}"
        if location != "Remote":
            indeed_url += f"&l={location_encoded}"
        urls["Indeed"] = indeed_url

        # Glassdoor
        glassdoor_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role_encoded}"
        urls["Glassdoor"] = glassdoor_url

        # Remote job boards (if remote)
        if remote:
            # Remote.co
            urls["Remote.co"] = f"https://remote.co/remote-jobs/search/?search_keywords={role_encoded}"

            # WeWorkRemotely
            wwr_category = self._get_wwr_category(role)
            urls["WeWorkRemotely"] = f"https://weworkremotely.com/remote-jobs/search?term={role_encoded}"

        return urls

    def _get_wwr_category(self, role: str) -> str:
        """Map role to WeWorkRemotely category."""
        role_lower = role.lower()

        if any(word in role_lower for word in ["engineer", "developer", "architect"]):
            return "engineering"
        elif any(word in role_lower for word in ["sales", "business", "account"]):
            return "sales-and-marketing"
        elif any(word in role_lower for word in ["design", "ux", "ui"]):
            return "design"
        else:
            return "all-categories"

    def generate_search_query(
        self,
        role: str,
        location: str = "Europe",
        company_type: str = "SaaS",
        additional_keywords: Optional[List[str]] = None
    ) -> str:
        """
        Generate a web search query for finding jobs.

        Args:
            role: Job title
            location: Location
            company_type: Company type (e.g., "SaaS", "Fintech")
            additional_keywords: Extra keywords

        Returns:
            Search query string
        """
        keywords = [role, location, company_type, "jobs", "2026"]

        if additional_keywords:
            keywords.extend(additional_keywords)

        return " ".join(keywords)

    def parse_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from job URL."""
        from urllib.parse import urlparse

        domain = urlparse(url).netloc

        # Remove common prefixes
        domain = domain.replace("www.", "").replace("jobs.", "").replace("careers.", "")

        # Remove TLD
        company = domain.split(".")[0]

        return company.title()


def search_jobs_for_target_companies(
    target_companies: List[str],
    role: str = "Solutions Engineer"
) -> Dict[str, List[str]]:
    """
    Search for jobs at specific target companies.

    Args:
        target_companies: List of company names
        role: Role to search for

    Returns:
        Dictionary of {company: [job_urls]}
    """
    results = {}

    for company in target_companies:
        # Build search URLs
        urls = {
            "LinkedIn": f"https://www.linkedin.com/jobs/search/?keywords={role}%20{company}",
            "Wellfound": f"https://wellfound.com/company/{company.lower().replace(' ', '-')}/jobs",
            "Company Careers": f"https://{company.lower().replace(' ', '')}.com/careers"
        }

        results[company] = list(urls.values())

    return results


def get_popular_job_boards() -> List[Dict[str, str]]:
    """Get list of popular job boards with URLs."""
    return [
        {
            "name": "LinkedIn Jobs",
            "url": "https://www.linkedin.com/jobs/",
            "description": "Largest professional network, best for SaaS roles",
            "best_for": "All roles, especially technical"
        },
        {
            "name": "Wellfound (AngelList)",
            "url": "https://wellfound.com/jobs",
            "description": "Startup and scale-up focused",
            "best_for": "Startups, Sales Engineer, BDR"
        },
        {
            "name": "Indeed",
            "url": "https://www.indeed.com/",
            "description": "General job board with wide coverage",
            "best_for": "All roles, high volume"
        },
        {
            "name": "Remote.co",
            "url": "https://remote.co/remote-jobs/",
            "description": "Remote-only positions",
            "best_for": "Remote work"
        },
        {
            "name": "WeWorkRemotely",
            "url": "https://weworkremotely.com/",
            "description": "Remote jobs in tech",
            "best_for": "Remote tech roles"
        },
        {
            "name": "Glassdoor",
            "url": "https://www.glassdoor.com/Job/",
            "description": "Jobs with company reviews",
            "best_for": "Company research + jobs"
        },
        {
            "name": "Built In",
            "url": "https://builtin.com/jobs",
            "description": "Tech jobs by location",
            "best_for": "Tech roles in specific cities"
        },
        {
            "name": "The Muse",
            "url": "https://www.themuse.com/jobs",
            "description": "Company culture focused",
            "best_for": "Culture-fit focused search"
        }
    ]
