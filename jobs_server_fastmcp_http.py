"""
Jobs Database MCP Server - Official FastMCP with Streamable HTTP
Based on https://modelcontextprotocol.io/docs/develop/build-server

Uses FastMCP with streamable-http transport for n8n integration.
"""

import logging
import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("jobs-database")

# Existing SQLite DB (do not recreate)
DB_PATH = Path(__file__).parent / "jobs.db"


def get_db_connection():
    """Get a connection to the existing SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def search_jobs(keyword: str, location: str) -> str:
    """Search for jobs by keyword and location.
    
    This tool searches the jobs database for positions matching the given
    keyword and location. Results are formatted and returned as a string.
    
    Args:
        keyword: Job keyword to search for (e.g., 'python', 'data', 'devops')
        location: Job location to filter by (e.g., 'Paris', 'London', 'Berlin')
    
    Returns:
        A formatted string with matching job listings or a message if no jobs found.
    """
    try:
        logger.info(f"Searching jobs: keyword='{keyword}', location='{location}'")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT title, job_title, jk, company, location, canonical, contract, description, created_at
            FROM jobs
            WHERE (LOWER(title) LIKE LOWER(?)
               OR LOWER(job_title) LIKE LOWER(?)
               OR LOWER(company) LIKE LOWER(?)
               OR LOWER(description) LIKE LOWER(?))
            AND LOWER(location) LIKE LOWER(?)
            ORDER BY created_at DESC
        """

        search_keyword = f"%{keyword}%"
        search_location = f"%{location}%"

        cursor.execute(
            query,
            (search_keyword, search_keyword, search_keyword, search_keyword, search_location),
        )
        jobs = cursor.fetchall()
        conn.close()
        
        if not jobs:
            return f"No jobs found for keyword '{keyword}' in location '{location}'."
        
        results = []
        for i, job in enumerate(jobs, 1):
            job_info = f"""
Job {i}:
  Title: {job['title'] or job['job_title']}
  Job Title: {job['job_title']}
  Company: {job['company']}
  Location: {job['location']}
  Description: {job['description']}
  Contract: {job['contract']}
  Canonical: {job['canonical']}
  JK: {job['jk']}
  Created At: {job['created_at']}"""
            results.append(job_info)
        
        output = f"Found {len(jobs)} job(s):\n" + "\n" + "-" * 60 + "\n".join(results)
        logger.info(f"Search completed: found {len(jobs)} jobs")
        return output
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}", exc_info=True)
        return f"Error searching jobs: {str(e)}"


@mcp.tool()
def get_user_profile(name: str) -> str:
    """Get a user profile by name from the existing SQLite database."""
    try:
        logger.info(f"Retrieving profile for user: '{name}'")

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT name, experience, education, location,
                   skills_json, languages_json, interests_json
            FROM user_profile
            WHERE LOWER(name) = LOWER(?)
        """

        cursor.execute(query, (name,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            logger.info(f"User '{name}' not found")
            return f"User '{name}' not found in the database."

        profile = f"""User Profile:
  Name: {user['name']}
  Experience: {user['experience']}
  Education: {user['education']}
  Location: {user['location']}
  Skills: {user['skills_json']}
  Languages: {user['languages_json']}
  Interests: {user['interests_json']}"""

        logger.info(f"Profile retrieved for user: {name}")
        return profile

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}", exc_info=True)
        return f"Error retrieving user profile: {str(e)}"


def main():
    """Initialize database and run the MCP server with streamable-http transport.
    
    FastMCP streamable-http provides HTTP transport for MCP clients like n8n.
    """
    logger.info("=" * 70)
    logger.info("Starting Jobs Database MCP Server (existing SQLite)")
    logger.info(f"DB: {DB_PATH}")
    logger.info("Transport: Streamable HTTP")
    logger.info("Ready to accept HTTP connections from n8n")
    logger.info("=" * 70)
    
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
