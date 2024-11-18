#-------------------------------------------------------------------
# Nathaniel Dale
# crawler.py
# crawls cpp website content and stores in mongoDB
# cs4250 - Assignment #3 Q5
#-------------------------------------------------------------------

import urllib.request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pymongo import MongoClient

# mongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["cs_crawler"]
pages_collection = db["pages"]

# starting URL and target heading
start_url = "https://www.cpp.edu/sci/computer-science/"
target_heading = "Permanent Faculty"

# helper functions
def retrieveHTML(url):
    """Retrieve the HTML content of a URL."""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Error retrieving {url}: {e}")
        return None

def storePage(url, html, is_target=False):
    """Store a page in MongoDB."""
    pages_collection.update_one(
        {"url": url},
        {"$set": {"url": url, "html": html, "target": is_target}},
        upsert=True
    )

def parse(html):
    """Parse HTML content using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    return soup

def target_page(soup):
    """Check if a page is the target page based on the heading."""
    heading = soup.find("h1", class_="cpp-h1")
    return heading and heading.text.strip() == target_heading

# main crawler logic
def crawlerThread(frontier):
    """Crawl through pages starting from the frontier until the target is found."""
    visited = set()

    while frontier:
        url = frontier.pop(0)
        if url in visited:
            continue

        visited.add(url)
        print(f"Visiting: {url}")

        html = retrieveHTML(url)
        if not html:
            continue

        soup = parse(html)

        # check if the current page is the target page
        if target_page(soup):
            print(f"Target page found: {url}")
            storePage(url, html, is_target=True)  # save with target flag
            break

        storePage(url, html)  # save other pages without the target flag

        # extract and normalize links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(url, href)
            if absolute_url not in visited and absolute_url.endswith((".html", ".shtml")):
                frontier.append(absolute_url)

# start the crawler
if __name__ == "__main__":
    frontier = [start_url]
    crawlerThread(frontier)
