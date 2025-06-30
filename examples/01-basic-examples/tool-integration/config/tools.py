"""
Advanced tool definitions for Tool Integration example.

Demonstrates integration with external APIs, databases, web scraping,
and other advanced tool patterns.
"""

import asyncio
import aiohttp
import json
import sqlite3
import os
from typing import Dict, List, Any
from datetime import datetime
import logging

from tframex import TFrameXApp

logger = logging.getLogger("tool-integration.tools")


def setup_tools(app: TFrameXApp):
    """Configure all tools for the Tool Integration example."""
    
    # === External API Tools ===
    
    @app.tool(description="Gets current weather information for a city using OpenWeatherMap API")
    async def get_weather(city: str) -> str:
        """
        Get current weather for a city using OpenWeatherMap API.
        
        Args:
            city: Name of the city
            
        Returns:
            Weather information or error message
        """
        try:
            # Using a mock weather API for demo purposes
            # In production, you'd use: api_key = os.getenv("OPENWEATHER_API_KEY")
            mock_weather_data = {
                "london": {"temp": 15, "condition": "Cloudy", "humidity": 65},
                "paris": {"temp": 18, "condition": "Sunny", "humidity": 45},
                "tokyo": {"temp": 22, "condition": "Rainy", "humidity": 80},
                "new york": {"temp": 12, "condition": "Partly Cloudy", "humidity": 55}
            }
            
            city_lower = city.lower()
            if city_lower in mock_weather_data:
                data = mock_weather_data[city_lower]
                return f"Weather in {city}: {data['temp']}°C, {data['condition']}, Humidity: {data['humidity']}%"
            else:
                return f"Weather data for {city} not available in demo mode"
                
        except Exception as e:
            return f"Error getting weather data: {str(e)}"
    
    
    @app.tool(description="Gets latest news headlines for a topic")
    async def get_news(topic: str, limit: int = 5) -> str:
        """
        Get latest news headlines for a topic.
        
        Args:
            topic: News topic to search for
            limit: Number of headlines to return
            
        Returns:
            News headlines or error message
        """
        try:
            # Mock news data for demo
            mock_news = {
                "artificial intelligence": [
                    "New AI breakthrough in natural language processing",
                    "Tech giants invest billions in AI research",
                    "AI ethics guidelines released by industry leaders",
                    "Machine learning improves medical diagnoses",
                    "AI-powered climate models show promising results"
                ],
                "technology": [
                    "Quantum computing reaches new milestone",
                    "Electric vehicle adoption accelerates globally",
                    "Renewable energy costs continue to decline",
                    "5G networks expand to rural areas",
                    "Cybersecurity threats evolve with new technology"
                ],
                "business": [
                    "Global markets show steady growth",
                    "Remote work trends reshape office spaces",
                    "Sustainable business practices gain momentum",
                    "Supply chain innovations reduce costs",
                    "Digital transformation accelerates in traditional industries"
                ]
            }
            
            topic_lower = topic.lower()
            headlines = []
            
            # Find matching topics
            for key, news_list in mock_news.items():
                if topic_lower in key or key in topic_lower:
                    headlines.extend(news_list)
            
            if not headlines:
                headlines = mock_news.get("technology", [])
            
            selected_headlines = headlines[:limit]
            
            result = f"Latest news about '{topic}':\n"
            for i, headline in enumerate(selected_headlines, 1):
                result += f"{i}. {headline}\n"
            
            return result
            
        except Exception as e:
            return f"Error getting news: {str(e)}"
    
    
    @app.tool(description="Sends an email notification (simulated)")
    async def send_email(to: str, subject: str, body: str) -> str:
        """
        Send an email notification (simulated for demo).
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            Success or error message
        """
        try:
            # In production, you'd integrate with actual email service
            # For demo, we'll just log and confirm
            logger.info(f"Email sent to {to}: {subject}")
            
            # Simulate email sending delay
            await asyncio.sleep(1)
            
            return f"Email sent successfully to {to} with subject '{subject}'"
            
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    
    # === Database Tools ===
    
    @app.tool(description="Creates a SQLite database table")
    async def create_table(table_name: str, schema: str) -> str:
        """
        Create a SQLite database table.
        
        Args:
            table_name: Name of the table to create
            schema: SQL schema definition
            
        Returns:
            Success or error message
        """
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            conn = sqlite3.connect("data/example.db")
            cursor = conn.cursor()
            
            # Create table
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
            cursor.execute(create_sql)
            
            conn.commit()
            conn.close()
            
            return f"Table '{table_name}' created successfully"
            
        except Exception as e:
            return f"Error creating table: {str(e)}"
    
    
    @app.tool(description="Inserts data into a database table")
    async def insert_data(table_name: str, data: str) -> str:
        """
        Insert data into a database table.
        
        Args:
            table_name: Name of the table
            data: JSON string of data to insert
            
        Returns:
            Success or error message
        """
        try:
            conn = sqlite3.connect("data/example.db")
            cursor = conn.cursor()
            
            # Parse JSON data
            record = json.loads(data)
            
            # Generate INSERT statement
            columns = list(record.keys())
            placeholders = ["?" for _ in columns]
            values = list(record.values())
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            
            return f"Data inserted into '{table_name}' successfully"
            
        except Exception as e:
            return f"Error inserting data: {str(e)}"
    
    
    @app.tool(description="Queries data from a database table")
    async def query_data(table_name: str, condition: str = "") -> str:
        """
        Query data from a database table.
        
        Args:
            table_name: Name of the table to query
            condition: Optional WHERE condition
            
        Returns:
            Query results or error message
        """
        try:
            conn = sqlite3.connect("data/example.db")
            cursor = conn.cursor()
            
            # Build query
            query = f"SELECT * FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            conn.close()
            
            if not results:
                return f"No data found in table '{table_name}'"
            
            # Format results
            result_str = f"Results from '{table_name}':\n"
            result_str += " | ".join(columns) + "\n"
            result_str += "-" * (len(" | ".join(columns))) + "\n"
            
            for row in results:
                result_str += " | ".join(str(val) for val in row) + "\n"
            
            return result_str
            
        except Exception as e:
            return f"Error querying data: {str(e)}"
    
    
    # === Web Scraping Tools ===
    
    @app.tool(description="Scrapes content from a web page")
    async def scrape_webpage(url: str) -> str:
        """
        Scrape content from a web page.
        
        Args:
            url: URL of the web page to scrape
            
        Returns:
            Scraped content or error message
        """
        try:
            # For demo purposes, simulate web scraping
            # In production, you'd use aiohttp and BeautifulSoup
            
            mock_content = {
                "python.org": "Python is a programming language that lets you work more quickly and integrate your systems more effectively.",
                "github.com": "GitHub is where developers shape the future of software together.",
                "stackoverflow.com": "Stack Overflow is the largest, most trusted online community for developers to learn and share their knowledge.",
                "docs.python.org": "Welcome to the official Python documentation. Python is an easy to learn, powerful programming language."
            }
            
            # Extract domain for mock lookup
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            
            for mock_domain, content in mock_content.items():
                if mock_domain in domain:
                    return f"Content from {url}:\n{content}"
            
            return f"Demo content for {url}: This is simulated web scraping content. In production, this would fetch real content from the URL."
            
        except Exception as e:
            return f"Error scraping webpage: {str(e)}"
    
    
    @app.tool(description="Downloads and saves a file from a URL")
    async def download_file(url: str, filename: str) -> str:
        """
        Download and save a file from a URL.
        
        Args:
            url: URL of the file to download
            filename: Local filename to save as
            
        Returns:
            Success or error message
        """
        try:
            # For demo, create a mock file
            os.makedirs("data/downloads", exist_ok=True)
            
            filepath = f"data/downloads/{filename}"
            
            # Simulate download
            mock_content = f"Mock downloaded content from {url}\nDownloaded at: {datetime.now().isoformat()}"
            
            with open(filepath, "w") as f:
                f.write(mock_content)
            
            return f"File downloaded and saved as '{filepath}'"
            
        except Exception as e:
            return f"Error downloading file: {str(e)}"
    
    
    # === File Processing Tools ===
    
    @app.tool(description="Processes a CSV file and returns statistics")
    async def process_csv(filename: str) -> str:
        """
        Process a CSV file and return basic statistics.
        
        Args:
            filename: Name of the CSV file to process
            
        Returns:
            Processing results or error message
        """
        try:
            # For demo, create and process a mock CSV
            if not os.path.exists(filename):
                # Create sample CSV
                sample_data = """Name,Age,City,Salary
John Doe,30,New York,75000
Jane Smith,25,Los Angeles,65000
Bob Johnson,35,Chicago,80000
Alice Brown,28,Houston,70000
Charlie Davis,32,Phoenix,72000"""
                
                with open(filename, "w") as f:
                    f.write(sample_data)
            
            # Read and process
            with open(filename, "r") as f:
                lines = f.readlines()
            
            headers = lines[0].strip().split(",")
            data_lines = lines[1:]
            
            stats = f"CSV Processing Results for '{filename}':\n"
            stats += f"- Total rows: {len(data_lines)}\n"
            stats += f"- Columns: {', '.join(headers)}\n"
            stats += f"- Sample data preview:\n"
            
            for i, line in enumerate(data_lines[:3]):
                stats += f"  Row {i+1}: {line.strip()}\n"
            
            return stats
            
        except Exception as e:
            return f"Error processing CSV: {str(e)}"
    
    
    @app.tool(description="Generates a report and saves it to a file")
    async def generate_report(title: str, content: str, format: str = "txt") -> str:
        """
        Generate a report and save it to a file.
        
        Args:
            title: Report title
            content: Report content
            format: File format (txt, md, html)
            
        Returns:
            Success or error message
        """
        try:
            os.makedirs("data/reports", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/reports/{title.lower().replace(' ', '_')}_{timestamp}.{format}"
            
            if format == "md":
                report_content = f"# {title}\n\n{content}\n\n---\nGenerated: {datetime.now().isoformat()}"
            elif format == "html":
                report_content = f"""<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
<p>{content}</p>
<hr>
<p><em>Generated: {datetime.now().isoformat()}</em></p>
</body>
</html>"""
            else:  # txt
                report_content = f"{title}\n{'=' * len(title)}\n\n{content}\n\nGenerated: {datetime.now().isoformat()}"
            
            with open(filename, "w") as f:
                f.write(report_content)
            
            return f"Report '{title}' generated and saved as '{filename}'"
            
        except Exception as e:
            return f"Error generating report: {str(e)}"