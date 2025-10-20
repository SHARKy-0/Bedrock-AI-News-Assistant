import os
import requests
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
import time
from urllib.parse import urlparse

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Google Custom Search API Key
GOOGLE_CX = os.getenv("GOOGLE_CX")            # Custom Search Engine ID

def google_search(query, num_results=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": num_results
    }
    res = requests.get(url, params=params)
    results = []
    if res.status_code == 200:
        data = res.json()
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })
    else:
        print("Google Search Error:", res.text)
    return results

def extract_article_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    if article:
        text = " ".join(p.get_text() for p in article.find_all("p"))
    else:
        text = " ".join(p.get_text() for p in soup.find_all("p"))
    return text

def fetch_site_content(keyword, site=None, max_results=5):
    print(f"--- 1. Fetching news list for '{keyword}' from Google Search ---")
    
    query = keyword 

    if site:
        # Case A: user specified a site
        if "http" in site:
            site_domain = urlparse(site).netloc
            site = site_domain
        if site:
            query += f" site:{site}"
    else:
        # Case B: user did not specify a site, use default list
        query += " (site:bbc.com OR site:worldjournal.com OR site:nyt.com OR site:reuters.com)"
            
    print(f"Generated Google search query: {query}")
    search_results = google_search(query, num_results=max_results)
    print(f"--- Google Search returned {len(search_results)} results ---")
    
    if not search_results:
        return []  

    print(f"\n--- 2. Start scraping full content for {len(search_results)} articles ---")
    all_news = [] 
    
    for r in search_results:
        print(f"\nProcessing: {r['title']}")

        news_content = extract_article_text(r['link'])
        print(f"  ... Content preview: {news_content[:100]}...")
        
        all_news.append({
            "title": r["title"],
            "link": r["link"],
            "snippet": r["snippet"],
            "content": news_content 
        })
        time.sleep(1)

    return all_news
