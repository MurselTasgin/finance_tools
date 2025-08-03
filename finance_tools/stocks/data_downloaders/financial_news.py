"""Financial news search tool for stock-specific news using free alternatives."""

import requests
import json
import time
import random
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import re
from bs4 import BeautifulSoup

 
from .base_tool import BaseTool, ToolResult, ToolArgument, ToolCapability, ToolArgumentType, register_tool

class FinancialNewsDownloader():
    """Tool for searching financial news for specific stocks using free sources."""
    
    def __init__(self):
        super().__init__(
            name="financial_news_search",
            description="Search and retrieve real-time financial news articles, press releases, and market updates about specific stock symbols or companies from multiple trusted financial news sources including Yahoo Finance, MarketWatch, and Seeking Alpha.",
            version="1.0.0"
        )
        self._setup_arguments()
        self._setup_capabilities()
        self._session = None
    
    def _setup_arguments(self):
        """Setup tool arguments."""
        self.add_argument(ToolArgument(
            name="symbol",
            type=ToolArgumentType.STRING,
            description="Stock symbol to search news for (e.g., 'AAPL', 'MSFT')",
            required=True
        ))
        
        self.add_argument(ToolArgument(
            name="max_results",
            type=ToolArgumentType.INTEGER,
            description="Maximum number of news articles to return",
            required=False,
            default=20,
            min_value=1,
            max_value=100
        ))
        
        self.add_argument(ToolArgument(
            name="days_back",
            type=ToolArgumentType.INTEGER,
            description="Number of days back to search for news",
            required=False,
            default=7,
            min_value=1,
            max_value=90
        ))
        
        self.add_argument(ToolArgument(
            name="sources",
            type=ToolArgumentType.LIST,
            description="Preferred news sources (yahoo, marketwatch, seeking_alpha, reuters, bloomberg)",
            required=False,
            default=["yahoo", "marketwatch", "seeking_alpha"]
        ))
        
        self.add_argument(ToolArgument(
            name="include_content",
            type=ToolArgumentType.BOOLEAN,
            description="Include article content/summary if available",
            required=False,
            default=True
        ))
        
        self.add_argument(ToolArgument(
            name="sort_by",
            type=ToolArgumentType.STRING,
            description="Sort results by date or relevance",
            required=False,
            default="date",
            choices=["date", "relevance"]
        ))
        
        self.add_argument(ToolArgument(
            name="language",
            type=ToolArgumentType.STRING,
            description="Language for news articles",
            required=False,
            default="en",
            choices=["en", "es", "fr", "de", "it", "pt"]
        ))
        
        self.add_argument(ToolArgument(
            name="timeout",
            type=ToolArgumentType.INTEGER,
            description="Request timeout in seconds",
            required=False,
            default=30,
            min_value=5,
            max_value=120
        ))
    
    def _setup_capabilities(self):
        """Setup tool capabilities."""
        self.add_capability(ToolCapability(
            name="stock_specific_news",
            description="Search for news articles about specific stocks",
            input_types=[ToolArgumentType.STRING],
            output_type="list",
            examples=[
                "symbol='AAPL' -> Latest Apple Inc. news articles",
                "symbol='TSLA' -> Tesla news and analysis"
            ]
        ))
        
        self.add_capability(ToolCapability(
            name="multi_source_aggregation",
            description="Aggregate news from multiple financial sources",
            input_types=[ToolArgumentType.STRING, ToolArgumentType.LIST],
            output_type="list",
            examples=[
                "sources=['yahoo', 'marketwatch'] -> News from Yahoo Finance and MarketWatch"
            ]
        ))
        
        self.add_capability(ToolCapability(
            name="time_filtered_news",
            description="Filter news by time period",
            input_types=[ToolArgumentType.STRING, ToolArgumentType.INTEGER],
            output_type="list",
            examples=[
                "symbol='AAPL', days_back=1 -> Today's Apple news",
                "symbol='MSFT', days_back=30 -> Last month's Microsoft news"
            ]
        ))
    
    def _setup_tool(self):
        """Setup tool-specific configurations."""
        self._session = requests.Session()
        
        # Set up headers to mimic a real browser
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Define source configurations
        self._source_configs = {
            'yahoo': {
                'name': 'Yahoo Finance',
                'search_url': 'https://finance.yahoo.com/quote/{symbol}/news',
                'parser': self._parse_yahoo_news
            },
            'marketwatch': {
                'name': 'MarketWatch',
                'search_url': 'https://www.marketwatch.com/investing/stock/{symbol}',
                'parser': self._parse_marketwatch_news
            },
            'seeking_alpha': {
                'name': 'Seeking Alpha',
                'search_url': 'https://seekingalpha.com/symbol/{symbol}/news',
                'parser': self._parse_seeking_alpha_news
            },
            'reuters': {
                'name': 'Reuters',
                'search_url': 'https://www.reuters.com/companies/{symbol}',
                'parser': self._parse_reuters_news
            },
            'bloomberg': {
                'name': 'Bloomberg',
                'search_url': 'https://www.bloomberg.com/quote/{symbol}:US',
                'parser': self._parse_bloomberg_news
            }
        }
    
    def execute(self, **kwargs) :
        """Execute financial news search."""
        start_time = time.time()
        
        try:
            validated_args = self.validate_arguments(**kwargs)
            
            symbol = validated_args["symbol"].upper().strip()
            max_results = validated_args.get("max_results", 20)
            days_back = validated_args.get("days_back", 7)
            sources = validated_args.get("sources", ["yahoo", "marketwatch", "seeking_alpha"])
            include_content = validated_args.get("include_content", True)
            sort_by = validated_args.get("sort_by", "date")
            language = validated_args.get("language", "en")
            timeout = validated_args.get("timeout", 30)
            
            if not symbol:
                return ToolResult(
                    success=False,
                    error="Stock symbol cannot be empty"
                )
            
            # Collect news from all specified sources
            all_news = []
            source_results = {}
            
            for source in sources:
                if source in self._source_configs:
                    try:
                        news_items = self._search_source(source, symbol, days_back, timeout)
                        if news_items:
                            all_news.extend(news_items)
                            source_results[source] = len(news_items)
                        
                        # Add delay between source requests
                        time.sleep(random.uniform(1.0, 2.0))
                        
                    except Exception as e:
                        print(f"Warning: Failed to get news from {source}: {e}")
                        source_results[source] = 0
                else:
                    print(f"Warning: Unknown news source '{source}' skipped")
            
            # Remove duplicates based on title similarity
            unique_news = self._remove_duplicates(all_news)
            
            # Sort results
            if sort_by == "date":
                unique_news = sorted(unique_news, key=lambda x: x.get('published_date', ''), reverse=True)
            elif sort_by == "relevance":
                unique_news = sorted(unique_news, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Limit results
            final_results = unique_news[:max_results]
            
            # Enhance with content if requested
            if include_content:
                final_results = self._enhance_with_content(final_results, timeout)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                data=final_results,
                metadata={
                    "symbol": symbol,
                    "total_articles": len(final_results),
                    "max_results": max_results,
                    "days_back": days_back,
                    "sources_searched": sources,
                    "source_results": source_results,
                    "duplicates_removed": len(all_news) - len(unique_news),
                    "sort_by": sort_by,
                    "include_content": include_content,
                    "search_period": f"{days_back} days"
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Financial news search failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _search_source(self, source: str, symbol: str, days_back: int, timeout: int) -> List[Dict[str, Any]]:
        """Search a specific news source."""
        
        config = self._source_configs[source]
        url = config['search_url'].format(symbol=symbol)
        parser = config['parser']
        
        try:
            response = self._session.get(url, timeout=timeout)
            response.raise_for_status()
            
            news_items = parser(response.text, symbol, days_back)
            
            # Add source information to each item
            for item in news_items:
                item['source'] = config['name']
                item['source_key'] = source
            
            return news_items
            
        except Exception as e:
            raise Exception(f"Failed to search {source}: {str(e)}")
    
    def _parse_yahoo_news(self, html_content: str, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Parse Yahoo Finance news."""
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # Yahoo Finance news structure
        news_sections = soup.find_all(['li', 'div'], class_=re.compile(r'js-stream-content|story-wrap'))
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for section in news_sections:
            try:
                # Extract title and link
                title_elem = section.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href')
                
                if link and not link.startswith('http'):
                    link = 'https://finance.yahoo.com' + link
                
                # Extract summary/snippet
                summary_elem = section.find('p') or section.find('div', class_=re.compile(r'summary|snippet'))
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                # Extract date
                date_elem = section.find('time') or section.find('span', class_=re.compile(r'date|time'))
                published_date = self._parse_date(date_elem.get_text(strip=True) if date_elem else '')
                
                # Check if article is within date range
                if published_date and self._parse_date_obj(published_date) < cutoff_date:
                    continue
                
                news_item = {
                    'title': title,
                    'url': link,
                    'summary': summary,
                    'published_date': published_date,
                    'relevance_score': self._calculate_relevance(title, summary, symbol)
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                continue
        
        return news_items[:20]  # Limit per source
    
    def _parse_marketwatch_news(self, html_content: str, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Parse MarketWatch news."""
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # MarketWatch news structure
        news_sections = soup.find_all(['div', 'article'], class_=re.compile(r'article|news-item'))
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for section in news_sections:
            try:
                title_elem = section.find('a', class_=re.compile(r'link|headline'))
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href')
                
                if link and not link.startswith('http'):
                    link = 'https://www.marketwatch.com' + link
                
                summary_elem = section.find('p', class_=re.compile(r'summary|description'))
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                date_elem = section.find('time') or section.find('span', class_=re.compile(r'timestamp|date'))
                published_date = self._parse_date(date_elem.get_text(strip=True) if date_elem else '')
                
                if published_date and self._parse_date_obj(published_date) < cutoff_date:
                    continue
                
                news_item = {
                    'title': title,
                    'url': link,
                    'summary': summary,
                    'published_date': published_date,
                    'relevance_score': self._calculate_relevance(title, summary, symbol)
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                continue
        
        return news_items[:20]
    
    def _parse_seeking_alpha_news(self, html_content: str, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Parse Seeking Alpha news."""
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # Seeking Alpha news structure
        news_sections = soup.find_all(['article', 'div'], class_=re.compile(r'article|news'))
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for section in news_sections:
            try:
                title_elem = section.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href')
                
                if link and not link.startswith('http'):
                    link = 'https://seekingalpha.com' + link
                
                summary_elem = section.find('span', class_=re.compile(r'summary|bullet'))
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                date_elem = section.find('time') or section.find('span', class_=re.compile(r'date'))
                published_date = self._parse_date(date_elem.get_text(strip=True) if date_elem else '')
                
                if published_date and self._parse_date_obj(published_date) < cutoff_date:
                    continue
                
                news_item = {
                    'title': title,
                    'url': link,
                    'summary': summary,
                    'published_date': published_date,
                    'relevance_score': self._calculate_relevance(title, summary, symbol)
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                continue
        
        return news_items[:20]
    
    def _parse_reuters_news(self, html_content: str, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Parse Reuters news (simplified)."""
        # Reuters has a more complex structure, this is a basic implementation
        return []
    
    def _parse_bloomberg_news(self, html_content: str, symbol: str, days_back: int) -> List[Dict[str, Any]]:
        """Parse Bloomberg news (simplified)."""
        # Bloomberg requires more sophisticated parsing, this is a basic implementation
        return []
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to standardized format."""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Common date patterns
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2}) hours? ago',
            r'(\d{1,2}) minutes? ago',
            r'(\d{1,2}) days? ago',
        ]
        
        date_str = date_str.lower().strip()
        
        # Handle relative dates
        if 'hours ago' in date_str:
            hours = int(re.search(r'(\d+)', date_str).group(1))
            result_date = datetime.now() - timedelta(hours=hours)
            return result_date.strftime('%Y-%m-%d %H:%M:%S')
        
        if 'minutes ago' in date_str:
            minutes = int(re.search(r'(\d+)', date_str).group(1))
            result_date = datetime.now() - timedelta(minutes=minutes)
            return result_date.strftime('%Y-%m-%d %H:%M:%S')
        
        if 'days ago' in date_str:
            days = int(re.search(r'(\d+)', date_str).group(1))
            result_date = datetime.now() - timedelta(days=days)
            return result_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Try to parse absolute dates
        try:
            # Try various formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
        except Exception:
            pass
        
        # Default to current time if parsing fails
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _parse_date_obj(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.now()
    
    def _calculate_relevance(self, title: str, summary: str, symbol: str) -> float:
        """Calculate relevance score for a news article."""
        score = 0.0
        
        text = (title + ' ' + summary).lower()
        symbol_lower = symbol.lower()
        
        # Direct symbol mention
        if symbol_lower in text:
            score += 1.0
        
        # Company name patterns (simplified)
        company_keywords = {
            'aapl': ['apple', 'iphone', 'ipad', 'mac'],
            'msft': ['microsoft', 'windows', 'azure', 'office'],
            'googl': ['google', 'alphabet', 'youtube', 'android'],
            'tsla': ['tesla', 'elon musk', 'electric vehicle', 'ev'],
            'amzn': ['amazon', 'aws', 'bezos', 'prime']
        }
        
        if symbol_lower in company_keywords:
            for keyword in company_keywords[symbol_lower]:
                if keyword in text:
                    score += 0.5
        
        # Financial keywords
        financial_terms = ['earnings', 'revenue', 'profit', 'stock', 'shares', 'dividend', 'acquisition', 'merger']
        for term in financial_terms:
            if term in text:
                score += 0.2
        
        return min(score, 2.0)  # Cap at 2.0
    
    def _remove_duplicates(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate news articles based on title similarity."""
        unique_items = []
        seen_titles = set()
        
        for item in news_items:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', item.get('title', '')).lower().strip()
            
            # Check if we've seen a very similar title
            is_duplicate = False
            for seen in seen_titles:
                if self._similarity_ratio(normalized_title, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
                seen_titles.add(normalized_title)
        
        return unique_items
    
    def _similarity_ratio(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _enhance_with_content(self, news_items: List[Dict[str, Any]], timeout: int) -> List[Dict[str, Any]]:
        """Enhance news items with additional content."""
        enhanced_items = []
        
        for item in news_items:
            enhanced_item = item.copy()
            
            try:
                if item.get('url'):
                    # Add delay between requests
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    response = self._session.get(
                        item['url'],
                        timeout=min(timeout, 10),
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Try to extract article content
                        content_selectors = [
                            'div[class*="content"]',
                            'div[class*="article"]',
                            'div[class*="body"]',
                            'section[class*="content"]',
                            'p'
                        ]
                        
                        for selector in content_selectors:
                            content_elements = soup.select(selector)
                            if content_elements:
                                content_text = ' '.join([elem.get_text(strip=True) for elem in content_elements[:3]])
                                if len(content_text) > 100:  # Only add if substantial content
                                    enhanced_item['content_preview'] = content_text[:500] + '...'
                                    break
                        
                        # Extract author if available
                        author_elem = soup.find('span', class_=re.compile(r'author|byline'))
                        if author_elem:
                            enhanced_item['author'] = author_elem.get_text(strip=True)
                
            except Exception as e:
                # Don't fail for content enhancement errors
                pass
            
            enhanced_items.append(enhanced_item)
        
        return enhanced_items


 

# Also create a function-based interface for easier use
@register_tool("search_stock_news")
def financial_news_search(symbol: str, max_results: int = 20, days_back: int = 7, **kwargs) -> List[Dict[str, Any]]:
    """
    Search for financial news about a specific stock.
    
    Args:
        symbol: Stock symbol to search for
        max_results: Maximum number of articles to return
        days_back: Number of days back to search
        **kwargs: Additional search parameters
    
    Returns:
        List of news articles with title, URL, summary, etc.
    """
    tool = FinancialNewsDownloader()
    result = tool.execute(
        symbol=symbol,
        max_results=max_results,
        days_back=days_back,
        **kwargs
    )
    
    if result.success:
        return result.data
    else:
        raise Exception(result.error)