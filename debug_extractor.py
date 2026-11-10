from shadowpurge.discovery import URLExtractor, ExtractedURL
import urllib.parse

# Test ExtractedURL directly
url = ExtractedURL(url='https://github.com/username')
print(f'Original URL: https://github.com/username')
print(f'Normalized URL: {url.url}')
print(f'Domain: {url.domain}')
print(f'Path: {url.path}')
print(f'Root domain: {url.root_domain}')
print(f'Platform hint: {url.platform_hint}')
print()

# Test with URL that has query params
url2 = ExtractedURL(url='https://github.com/username?utm_source=test')
print(f'Original URL: https://github.com/username?utm_source=test')
print(f'Normalized URL: {url2.url}')
print(f'Domain: {url2.domain}')
print(f'Path: {url2.path}')
print(f'Root domain: {url2.root_domain}')
print(f'Platform hint: {url2.platform_hint}')
print()

# Test the URLExtractor
extractor = URLExtractor()
urls = extractor.extract('Check out https://github.com/username and https://twitter.com/user123')
print(f'URLs found: {len(urls)}')
for url in urls:
    print(f'  URL: {url.url}, Domain: {url.domain}, Platform: {url.platform_hint}')

# Test reset
extractor.reset()
print(f'Cache cleared')