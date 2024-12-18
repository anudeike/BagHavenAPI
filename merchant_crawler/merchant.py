import json
from crawl_with_sitemap import BoxLunchSitemapCrawler
from process_products import ProductProcessor


pathToDomainsJSON = r"merchant_crawler\domains.json"
FIREBASE_CREDENTIALS = r'credentials\bag-haven-qt9s4v-firebase-adminsdk-h9x05-e584032402.json'

def read_domains(pathToDomainsJSON):

    domains = None

    try: 
        with open(pathToDomainsJSON, 'r') as f:
            domains = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{pathToDomainsJSON}' not found.")
        raise FileNotFoundError(f"Error: File '{pathToDomainsJSON}' not found.")

    return domains

def main():
    domains = None

    # read domains from domains.json file
    domains = read_domains(pathToDomainsJSON)

    print(f"Domains: {domains}")
    
    for domain in domains:

        domainBaseUrl = domain["base_url"]
        domainSitemapUrl = domain["sitemap_url"]

        print(f"Domain: {domainBaseUrl}")
        print(f"Sitemap: {domainSitemapUrl}")

        # Create BoxLunch sitemap crawler
        crawler = BoxLunchSitemapCrawler(domainBaseUrl, domainSitemapUrl)

        print(f"BoxLunch sitemap crawler created. With attributes: {crawler.__dict__}")

        # Crawl product sitemaps
        all_urls = crawler.crawl_product_sitemaps()

        # Filter product URLs
        product_urls = crawler.filter_product_urls(all_urls)

        # Print results
        print(f"Total URLs discovered: {len(all_urls)}")
        print(f"Product URLs: {len(product_urls)}")

        # for each of the product urls
        limit = -1

        if (limit < 0):
            limit = len(product_urls)

        processor = ProductProcessor(FIREBASE_CREDENTIALS)

        results = processor.process_product_urls(product_urls[:limit])

        # Print results
        print("\nProcessing Results:")
        for url, variants in results.items():
            print(f"\nURL: {url}")
            print("Variants:")
            for sku, product_id in variants.items():
                print(f"  SKU: {sku} -> Product ID: {product_id}")
        # for url in product_urls[:limit]:

        #     processor = ProductProcessor(FIREBASE_CREDENTIALS)
            
        #     results = processor.process_product_urls(product_urls)
            
        #     print("\nProcessing Results:")
        #     for url, variants in results.items():
        #         print(f"\nURL: {url}")
        #         print("Variants:")
        #         for sku, product_id in variants.items():
        #             print(f"  SKU: {sku} -> Product ID: {product_id}")
        #             print(f"URL: {url}")

        # get all the JSON LD data for each of the product urls

        # print the results
        


main()