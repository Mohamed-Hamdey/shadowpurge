import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_duckduckgo():
    url = "https://duckduckgo.com/html/?q=testuser+site:github.com+OR+site:twitter.com+OR+site:linkedin.com+OR+site:reddit.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://duckduckgo.com/html/?q=testuser", headers=headers, timeout=30.0, follow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for any links that contain platform URLs
        links = soup.find_all("a", href=True)
        print(f"Total links: {len(links)}")

        platform_domains = [
            'github.com', 'twitter.com', 'x.com', 'reddit.com', 'instagram.com',
            'linkedin.com', 'facebook.com', 'twitch.tv', 'spotify.com',
            'steamcommunity.com', 'pinterest.com', 'tiktok.com', 'discord.com',
            'youtube.com', 'medium.com', 'gitlab.com', 'bitbucket.org',
            'pypi.org', 'npmjs.com', 'dev.to', 'dribbble.com', 'behance.net',
            'flickr.com', 'tumblr.com', 'vimeo.com', 'soundcloud.com',
            'bandcamp.com', 'patreon.com', 'kofi.com', 'onlyfans.com',
            'about.me', 'gravatar.com', 'wordpress.com', 'substack.com'
        ]

        found_platforms = {}
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if href.startswith("http"):
                for domain in platform_domains:
                    if domain in href:
                        if domain not in found_platforms:
                            found_platforms[domain] = []
                        found_platforms[domain].append(href)

        if found_platforms:
            print("Found platforms:")
            for domain, urls in found_platforms.items():
                print(f"  {domain}: {len(urls)} URLs")
                for url in urls[:3]:
                    print(f"  - {url}")
        else:
            print("No platform URLs found in page")

if __name__ == "__main__":
    asyncio.run(test_duckduckgo())