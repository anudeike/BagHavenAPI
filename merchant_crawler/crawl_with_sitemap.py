import requests
import xml.etree.ElementTree as ET
import logging
from urllib.parse import urljoin, urlparse

class BoxLunchSitemapCrawler:
    def __init__(self, base_url='https://www.boxlunch.com', sitemap_url='sitemap_index.xml'):
        """
        Initialize BoxLunch sitemap crawler
        
        Args:
            base_url (str): Base URL of the website
        """
        self.sitemap_url = sitemap_url
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def extract_sitemap_urls(self, sitemap_url):
        """
        Extract URLs from a specific sitemap
        
        Args:
            sitemap_url (str): URL of the sitemap to crawl
        
        Returns:
            list: URLs extracted from the sitemap
        """
        try:
            # Fetch sitemap
            response = requests.get(sitemap_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.text)
            
            # Namespace handling
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Extract URLs
            urls = []
            
            # Check if it's a sitemap index or a regular sitemap
            if root.tag.endswith('sitemapindex'):
                # If it's a sitemap index, return the sitemap locations
                sitemap_locs = root.findall('.//ns:loc', namespace)
                urls = [loc.text.strip() for loc in sitemap_locs]
            else:
                # If it's a regular sitemap, extract URL locations
                url_elements = root.findall('.//ns:loc', namespace)
                urls = [url.text.strip() for url in url_elements]
            
            return urls
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching sitemap {sitemap_url}: {e}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Error parsing sitemap XML: {e}")
            return []

    def get_product_sitemaps(self, sitemap_index_url):
        """
        Extract product-specific sitemaps from the sitemap index
        
        Args:
            sitemap_index_url (str): URL of the sitemap index
        
        Returns:
            list: URLs of product-specific sitemaps
        """
        # Fetch sitemap index
        sitemaps = self.extract_sitemap_urls(sitemap_index_url)
        
        # Filter for product sitemaps
        product_sitemaps = [
            sitemap for sitemap in sitemaps 
            if '-product.xml' in sitemap
        ]
        
        return product_sitemaps

    def crawl_product_sitemaps(self):
        """
        Crawl all product sitemaps and extract product URLs
        
        Returns:
            list: Comprehensive list of product URLs
        """
        # Construct sitemap index URL
        sitemap_index_url = urljoin(self.base_url, self.sitemap_url)
        
        # Get product-specific sitemaps
        product_sitemaps = self.get_product_sitemaps(sitemap_index_url)
        
        # Collect all product URLs
        all_product_urls = []
        
        for sitemap in product_sitemaps:
            self.logger.info(f"Crawling sitemap: {sitemap}")
            product_urls = self.extract_sitemap_urls(sitemap)
            all_product_urls.extend(product_urls)
        
        # Remove duplicates
        unique_product_urls = list(set(all_product_urls))
        
        return unique_product_urls

    def filter_product_urls(self, urls):
        """
        Filter and validate product URLs
        
        Args:
            urls (list): List of URLs to filter
        
        Returns:
            list: Filtered product URLs
        """
        # Filter for valid product URLs
        valid_product_urls = [
            url for url in urls
            if '/product/' in url and url.startswith('https://www.boxlunch.com')
        ]
        
        return valid_product_urls

# Example usage
if __name__ == '__main__':
    # Create BoxLunch sitemap crawler
    crawler = BoxLunchSitemapCrawler()
    
    # Crawl product sitemaps
    all_urls = crawler.crawl_product_sitemaps()
    
    # Filter product URLs
    product_urls = crawler.filter_product_urls(all_urls)
    
    # Print results
    print(f"Total URLs discovered: {len(all_urls)}")
    print(f"Product URLs: {len(product_urls)}")
    
    # Optionally save to file
    with open('boxlunch_product_urls.txt', 'w') as f:
        for url in product_urls:
            f.write(f"{url}\n")
    
    # Print first few product URLs for verification
    print("\nSample Product URLs:")
    for url in product_urls[:10]:
        print(url)

    