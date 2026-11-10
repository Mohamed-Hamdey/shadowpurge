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

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to find all tables and their contents
        tables = soup.find_all("table")
        print(f"Tables found: {len(tables)}")

        for i, table in enumerate(tables):
            print(f"\nTable {i}:")
            rows = table.find_all("tr")
            print(f"  Rows: {len(rows)}")
            for j, row in enumerate(rows[:5]):
                cells = row.find_all(["td", "th"])
                cell_texts = [cell.get_text(strip=True)[:50] for cell in cells]
                print(f"  Row {j}: {cell_texts}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_duckduckgo())