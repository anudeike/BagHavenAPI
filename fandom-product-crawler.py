import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

class BoxLunchCrawler:
    def __init__(self, base_url='https://www.boxlunch.com/bags/mini-backpacks/?start=0&sz=100'):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_category_pages(self):
        """
        Retrieve all category pages from the main navigation
        
        Returns:
            list: URLs of category pages
        """
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find navigation links to product categories
            # Note: This selector might need adjustment based on BoxLunch's actual HTML structure
            category_links = soup.select('nav a[href*="/category/"]')
            
            # Convert relative URLs to absolute
            category_urls = [
                urljoin(self.base_url, link['href']) 
                for link in category_links 
                if link.get('href')
            ]
            
            return category_urls
        
        except requests.RequestException as e:
            print(f"Error fetching category pages: {e}")
            return []

    def extract_product_json_ld(self, product_url):
        """
        Extract JSON-LD data from a product page
        
        Args:
            product_url (str): URL of the product page
        
        Returns:
            dict: Parsed JSON-LD data or None
        """
        try:
            response = requests.get(product_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for JSON-LD script tags
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    json_ld_data = json.loads(script.string)
                    
                    # Filter for product JSON-LD
                    if isinstance(json_ld_data, dict) and json_ld_data.get('@type') == 'Product':
                        return json_ld_data
                except json.JSONDecodeError:
                    continue
            
            return None
        
        except requests.RequestException as e:
            print(f"Error fetching product page {product_url}: {e}")
            return None

    def get_products_from_category(self, category_url):
        """
        Retrieve product URLs from a category page
        
        Args:
            category_url (str): URL of the category page
        
        Returns:
            list: Product page URLs
        """
        try:
            response = requests.get(category_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product links 
            # Note: Selector might need adjustment based on actual site structure
            product_links = soup.select('a[href*="/product/"]')
            
            # Convert to absolute URLs
            product_urls = [
                urljoin(category_url, link['href']) 
                for link in product_links 
                if link.get('href')
            ]
            
            return product_urls
        
        except requests.RequestException as e:
            print(f"Error fetching category page {category_url}: {e}")
            return []

    def crawl(self):
        """
        Main crawling method
        
        Returns:
            list: Collected product JSON-LD data
        """

        
        all_products = []

        # get all of the products on the page
        
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all product tiles
            product_tiles = soup.find_all('div', class_='product-tile')
            
            # extract the product urls from the tiles
            product_urls = []
            
            for tile in product_tiles:
                # Find the image container within each product tile
                image_container = tile.find('div', class_='image-container')
                
                if image_container:
                    # Look for the link within the image container
                    link = image_container.find('a', class_='pdpLink')
                    
                    
                    if link and link.has_attr('href'):
                        # Convert relative URL to absolute URL
                        absolute_url = urljoin(self.base_url, link['href'])
                        print(f"Found product URL: {absolute_url}")
                        product_urls.append(absolute_url)
                    else:
                        print("No link found for product tile.")
                else:
                    print("No image container found for product tile.")
                    

            return product_urls
        
        except requests.RequestException as e:
            print(f"Error fetching category page {self.base_url}: {e}")
            return []
        # # Get category pages
        #category_urls = self.get_category_pages()
        
        # # For each category, get product URLs
        # for category_url in category_urls:
        #     product_urls = self.get_products_from_category(category_url)
            
        #     # Extract JSON-LD for each product
        #     for product_url in product_urls:
        #         product_json_ld = self.extract_product_json_ld(product_url)
        #         if product_json_ld:
        #             all_products.append(product_json_ld)
        
        return all_products

# Example usage
if __name__ == '__main__':
    crawler = BoxLunchCrawler()
    products = crawler.crawl()
    
    # Print or save the collected product data
    for product in products:
        print(json.dumps(product, indent=2))

    print(f"Total products collected: {len(products)}")