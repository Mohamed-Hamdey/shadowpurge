import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_duckduckgo():
    url = "https://duckduckgo.com/html/?q=testuser"
    headers = {"User-Agent": "ShadowPurge-Digital-Footprint-Scanner/1.0"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")

        # Save HTML for inspection
        with open("debug_ddg.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Try to parse
        soup = BeautifulSoup(response.text, "html.parser")

        # Try different selectors
        selectors = [
            ".result",
            ".results .result",
            ".web-result",
            ".result__snippet",
            "a.result__url",
            ".result__title",
            ".result__snippet",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            print(f"Selector '{selector}': {len(elements)} elements")

        # Print first 5000 chars of HTML for inspection
        print("\n--- HTML Preview ---")
        print(response.text[:5000])

if __name__ == "__main__":
    asyncio.run(test_duckduckgo())