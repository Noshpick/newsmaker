import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import asyncio
import re


class ContentFetcher:

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def fetch_article(self, url: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=30) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    html = await response.text()

            soup = BeautifulSoup(html, 'lxml')
            domain = urlparse(url).netloc
            title = self._extract_title(soup)
            content = self._extract_content(soup)

            return {
                'title': title,
                'content': content,
                'url': url,
                'domain': domain
            }

        except Exception as e:
            raise Exception(f"Ошибка при загрузке статьи: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title = None

        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']

        if not title and soup.title:
            title = soup.title.string

        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

        if not title:
            return "Без заголовка"

        title = self._clean_title(title)
        return title

    def _clean_title(self, title: str) -> str:
        if not title:
            return "Без заголовка"

        title = re.sub(r'\(@\w+\)', '', title)
        title = re.sub(r'@\w+', '', title)
        title = re.sub(r'\s*[—–-]\s*(Блог на|на)\s+[\w\.]+\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*[|\-–—]\s*(Новости|Статьи|Блог|Blog|News).*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'\(\s*\)', '', title)
        title = title.strip(' -–—|')

        return title or "Без заголовка"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        content_selectors = [
            'article',
            '[itemprop="articleBody"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main'
        ]

        content_text = ""

        for selector in content_selectors:
            content_block = soup.select_one(selector)
            if content_block:
                paragraphs = content_block.find_all(['p', 'h2', 'h3', 'li'])
                content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                if len(content_text) > 200:
                    break

        if len(content_text) < 200:
            paragraphs = soup.find_all('p')
            content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        return content_text or "Не удалось извлечь контент"

    async def test_url(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=self.headers, timeout=10) as response:
                    return response.status == 200
        except:
            return False


async def main():
    fetcher = ContentFetcher()
    article = await fetcher.fetch_article("https://example.com/article")
    print(article)


if __name__ == "__main__":
    asyncio.run(main())