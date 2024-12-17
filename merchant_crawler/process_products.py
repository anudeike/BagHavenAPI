import requests
from bs4 import BeautifulSoup
import json
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import logging
from typing import Optional, Dict, Any, List

class ProductProcessor:
    def __init__(self, firebase_credentials_path: str):
        """
        Initialize the product processor
        
        Args:
            firebase_credentials_path (str): Path to Firebase credentials JSON file
        """
        # Initialize Firebase
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Request headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract_json_ld(self, url: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract JSON-LD data from a product page
        
        Args:
            url (str): Product page URL
        
        Returns:
            list: List of JSON-LD data objects or None if not found
        """
        try:
            # Fetch the page
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find JSON-LD script tags
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                if script and script.string:
                    try:
                        json_ld_data = json.loads(script.string)
                        # Return as list if it's a list, otherwise wrap in list
                        return json_ld_data if isinstance(json_ld_data, list) else [json_ld_data]
                    except json.JSONDecodeError:
                        continue
            
            return None
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching product page {url}: {e}")
            return None

    def extract_products_from_json_ld(self, json_ld_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all product variants from JSON-LD data
        
        Args:
            json_ld_list (list): List of JSON-LD objects from the page
            
        Returns:
            list: List of processed product variant data
        """
        products = []
        
        for item in json_ld_list:
            # Check if this is a ProductGroup
            if isinstance(item, dict) and item.get('@type') == 'ProductGroup':
                # Base product information
                base_product = {
                    'groupId': item.get('productGroupID'),
                    'baseUrl': item.get('url'),
                    'baseName': item.get('name'),
                    'baseDescription': item.get('description'),
                    'baseImage': item.get('image'),
                    'variesBy': item.get('variesBy', [])
                }
                
                # Process each variant
                variants = item.get('hasVariant', [])
                for variant in variants:
                    if variant.get('@type') == 'Product':
                        variant_data = {
                            **base_product,  # Include base product info
                            'sku': variant.get('sku'),
                            'name': variant.get('name'),
                            'description': variant.get('description'),
                            'image': variant.get('image'),
                            'color': variant.get('color'),
                            'size': variant.get('size'),
                            'productUrl': variant.get('offers', {}).get('url'),
                            'price': variant.get('offers', {}).get('price'),
                            'priceCurrency': variant.get('offers', {}).get('priceCurrency'),
                            'availability': variant.get('offers', {}).get('availability'),
                            'type': 'variant'
                        }
                        products.append(variant_data)
        
        return products

    def generate_product_id(self) -> str:
        """
        Generate a unique product ID
        
        Returns:
            str: Unique product ID
        """
        return str(uuid.uuid4())

    def store_product_variants(self, variants_data: List[Dict[str, Any]], source_url: str) -> Dict[str, str]:
        """
        Store all product variants in Firebase
        
        Args:
            variants_data (list): List of product variants to store
            source_url (str): Original URL where the data was extracted from
            
        Returns:
            dict: Mapping of SKUs to their generated product IDs
        """
        results = {}
        
        try:
            # Create a batch write
            batch = self.db.batch()
            
            for variant in variants_data:
                # Generate product ID
                product_id = self.generate_product_id()
                
                # Add metadata
                enriched_data = {
                    'productId': product_id,
                    'sourceUrl': source_url,
                    'dateAdded': firestore.SERVER_TIMESTAMP,
                    **variant  # Include all variant data
                }
                
                # Add to batch
                doc_ref = self.db.collection('products').document(product_id)
                batch.set(doc_ref, enriched_data)
                
                # Store mapping of SKU to product ID
                results[variant['sku']] = product_id
            
            # Commit the batch
            batch.commit()
            
            self.logger.info(f"Successfully stored {len(variants_data)} variants")
            return results
        
        except Exception as e:
            self.logger.error(f"Error storing product variants in Firebase: {e}")
            return results

    def process_product_url(self, url: str) -> Dict[str, str]:
        """
        Process a single product URL - extract data and store in Firebase
        
        Args:
            url (str): Product URL to process
        
        Returns:
            dict: Mapping of SKUs to their generated product IDs
        """
        # Extract JSON-LD
        json_ld_data = self.extract_json_ld(url)
        
        if not json_ld_data:
            self.logger.warning(f"No valid JSON-LD found for {url}")
            return {}
        
        # Extract product variants
        variants = self.extract_products_from_json_ld(json_ld_data)
        
        if not variants:
            self.logger.warning(f"No product variants found for {url}")
            return {}
        
        # Store variants
        return self.store_product_variants(variants, url)

    def process_product_urls(self, urls: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Process multiple product URLs
        
        Args:
            urls (list): List of product URLs to process
        
        Returns:
            dict: Mapping of URLs to their variant results
        """
        results = {}
        
        for url in urls:
            variant_results = self.process_product_url(url)
            if variant_results:
                results[url] = variant_results
        
        return results

# Example usage
if __name__ == '__main__':
    # Path to your Firebase credentials JSON file
    FIREBASE_CREDENTIALS = r'credentials\bag-haven-qt9s4v-firebase-adminsdk-h9x05-e584032402.json'
    
    # Initialize processor
    processor = ProductProcessor(FIREBASE_CREDENTIALS)
    
    # Example URLs (replace with your actual URLs)
    product_urls = [
        'https://www.boxlunch.com/product/disney-lady-and-the-tramp-lineart-womens-t-shirt/14080919.html'
    ]
    
    # Process products
    results = processor.process_product_urls(product_urls)
    
    # Print results
    print("\nProcessing Results:")
    for url, variants in results.items():
        print(f"\nURL: {url}")
        print("Variants:")
        for sku, product_id in variants.items():
            print(f"  SKU: {sku} -> Product ID: {product_id}")