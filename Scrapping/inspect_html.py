import asyncio
from src.scraper.utils.http_client import http_client
from bs4 import BeautifulSoup

async def inspect_upheal():
    """Fetch Upheal pages and save HTML for inspection"""
    
    urls = [
        "https://www.upheal.io/features",
        "https://www.upheal.io/pricing"
    ]
    
    for url in urls:
        print(f"\n{'='*60}")
        print(f"Fetching: {url}")
        print(f"{'='*60}\n")
        
        try:
            # Fetch the page
            html = await http_client.fetch_text(url)
            
            # Save to file
            filename = url.split('/')[-1] + '.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ Saved to: {filename}")
            
            # Parse and show structure
            soup = BeautifulSoup(html, 'lxml')
            
            # Find potential feature containers
            print("\n🔍 Looking for feature-related elements...")
            feature_candidates = []
            for elem in soup.find_all(['div', 'section', 'article']):
                classes = elem.get('class', [])
                class_str = ' '.join(classes)
                if any(keyword in class_str.lower() for keyword in ['feature', 'card', 'item', 'benefit']):
                    feature_candidates.append(class_str)
            
            if feature_candidates:
                print(f"Found {len(feature_candidates)} potential containers:")
                for i, cls in enumerate(set(feature_candidates[:10]), 1):
                    print(f"  {i}. class=\"{cls}\"")
            
            # Find headings
            print("\n📝 Common heading patterns:")
            for tag in ['h1', 'h2', 'h3', 'h4']:
                headings = soup.find_all(tag, limit=5)
                if headings:
                    print(f"\n  {tag.upper()} tags:")
                    for h in headings[:3]:
                        classes = h.get('class', [])
                        text = h.get_text(strip=True)[:50]
                        print(f"    - class=\"{' '.join(classes)}\" → \"{text}...\"")
            
            await asyncio.sleep(2)  # Polite delay between requests
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_upheal())
