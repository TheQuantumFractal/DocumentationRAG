import requests
from bs4 import BeautifulSoup
import markdownify
import argparse
import os
import re

def extract_text(url: str):
    """Extract text from a webpage"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    article = soup.find('article')
    if article is not None:
        return markdownify.markdownify(str(article), heading_style="ATX")
    else:
        return None

def format_url(url: str, base_url: str):
    """Format a url to be absolute"""
    base_url = base_url.rstrip('/')
    if url.startswith('http'):
        return url
    elif url.startswith('/'):
        return base_url + url
    else:
        return base_url + '/' + url

def find_urls(url: str, base_url: str, visited: set):
    """Find urls on a webpage"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    urls = [format_url(link.get('href'), base_url) for link in links]
    urls = [link for link in urls if link not in visited and "#" not in link]
    return urls

def scrape(url: str, directory: str, base_url: str = None):
    """Scrape a webpage with BFS and save the text to a file"""
    if not base_url:
        base_url = "https://" + url.split('/')[2]
    visited = set()
    og_url = url
    to_visit = [url]
    while to_visit:
        url = to_visit.pop(0)
        if url not in visited and og_url in url:
            print(f'Visiting {url}')
            visited.add(url)
            text = extract_text(url)
            if text:
                text = re.sub("[\n]{2,}", "\n\n", text.replace("Copy", ""))
                filename = os.path.join(directory, f'{url.replace("/", "-")}_scraped.txt')
                with open(filename, 'w') as f:
                    f.write(text)
            to_visit.extend(find_urls(url, base_url, visited))

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--webpage', help='Webpage to start scraping from')
    argparser.add_argument('--directory', help='Directory to save the scraped data')
    argparser.add_argument('--base-url', required=False, default=None, 
                        help='Base url to start scraping from')

    args = argparser.parse_args()
    soup = scrape(args.webpage, args.directory, args.base_url)
    