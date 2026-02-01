#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web scraper for Indeed job listings
"""

import json
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import logging
import time
import io

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup logging
log_dir = Path(__file__).parent
log_file = log_dir / 'scraper.log'

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

JOBS_FILE = log_dir / "jobs_all.json"
INDEED_URL = "https://www.indeed.com/jobs"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def scrape_jobs(keyword: str, location: str = "Paris", num_pages: int = 1) -> list[dict]:
    """
    Scrape job listings from Indeed
    """
    jobs = []
    
    try:
        for page in range(num_pages):
            start = page * 10
            params = {
                "q": keyword,
                "l": location,
                "start": start,
                "limit": 10
            }
            
            headers = {"User-Agent": USER_AGENT}
            
            logging.info(f"Fetching page {page + 1} for keyword '{keyword}'")
            
            try:
                response = requests.get(
                    INDEED_URL,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse job listings
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    # Try alternative selector
                    job_cards = soup.find_all('div', {'data-testid': 'job-card'})
                
                for card in job_cards:
                    try:
                        # Extract job title
                        title_elem = card.find('h2', class_='jobTitle')
                        if not title_elem:
                            title_elem = card.find('span', {'class': lambda x: x and 'jobTitle' in x})
                        job_title = title_elem.get_text(strip=True) if title_elem else "N/A"
                        
                        # Extract company
                        company_elem = card.find('span', class_='companyName')
                        company = company_elem.get_text(strip=True) if company_elem else "N/A"
                        
                        # Extract location
                        location_elem = card.find('div', class_='companyLocation')
                        job_location = location_elem.get_text(strip=True) if location_elem else location
                        
                        # Extract salary (if available)
                        salary_elem = card.find('span', class_='salary-snippet')
                        salary = salary_elem.get_text(strip=True) if salary_elem else "Non spécifié"
                        
                        # Extract contract type
                        contract_elem = card.find('div', {'class': lambda x: x and 'contract-type' in x})
                        contract = contract_elem.get_text(strip=True) if contract_elem else "Non spécifié"
                        
                        # Extract job description snippet
                        desc_elem = card.find('div', class_='job-snippet')
                        description = desc_elem.get_text(strip=True) if desc_elem else "N/A"
                        
                        # Extract job URL
                        link_elem = card.find('a', class_='jcs-JobTitle')
                        if not link_elem:
                            link_elem = card.find('a', {'data-testid': 'job-link'})
                        job_url = link_elem.get('href', '#') if link_elem else "#"
                        if not job_url.startswith('http'):
                            job_url = f"https://www.indeed.com{job_url}"
                        
                        job = {
                            "job_title": job_title,
                            "company": company,
                            "location": job_location,
                            "salary": salary,
                            "contract": contract,
                            "description": description,
                            "url": job_url,
                            "keyword": keyword
                        }
                        
                        jobs.append(job)
                        logging.info(f"Scraped: {job_title} at {company}")
                    
                    except Exception as e:
                        logging.warning(f"Error parsing job card: {e}")
                        continue
                
                # Rate limiting
                time.sleep(2)
            
            except requests.RequestException as e:
                logging.error(f"Request error: {e}")
                break
    
    except Exception as e:
        logging.error(f"Scraping error: {e}")
    
    return jobs


def save_jobs(jobs: list[dict]):
    """Save jobs to JSON file"""
    try:
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(jobs)} jobs to {JOBS_FILE}")
    except Exception as e:
        logging.error(f"Error saving jobs: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        keyword = "Python Developer"
    else:
        keyword = sys.argv[1]
    
    location = sys.argv[2] if len(sys.argv) > 2 else "Paris"
    
    logging.info(f"Starting scraper for '{keyword}' in '{location}'")
    
    jobs = scrape_jobs(keyword, location, num_pages=2)
    
    if jobs:
        save_jobs(jobs)
        print(f"✅ {len(jobs)} jobs scraped and saved")
    else:
        print(f"⚠️ No jobs found for '{keyword}' in '{location}'")
    
    return len(jobs)


if __name__ == "__main__":
    main()
