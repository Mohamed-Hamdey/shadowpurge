import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_duckduckgo():
    url = "https://html.duckduckgo.com/html/?q=testuser"
    headers = {"User-Agent": "ShadowPurge-Digital-Footprint-Scanner/1.0"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")

        # Save HTML for inspection
        with open("debug_ddg2.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        soup = BeautifulSoup(response.text, "html.parser")

        # Try various selectors
        selectors = [
            ".result",
            ".results .result",
            ".web-result",
            "[data-result]",
            ".result__title",
            ".result__snippet",
            ".result__url",
            "a.result__url",
            "a[href]",
            "table tr",
            "tr",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Selector '{selector}': {len(elements)} elements")
                # Print first element
                if elements:
                    print(f"  First: {str(elements[0])[:200]}")
                    print()

if __name__ == "__main__":
    asyncio.run(test_duckduckgo())