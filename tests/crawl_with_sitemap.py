import requests

sitemap_url = "https://www.boxlunch.com/sitemap_index.xml"
response = requests.get(sitemap_url)

if response.status_code == 200:
    sitemap_content = response.text
else:
    print(f"Failed to fetch sitemap from {sitemap_url}")