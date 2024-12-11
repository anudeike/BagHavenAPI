from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import base64
import json
from bs4 import BeautifulSoup
import json
import time
import aiohttp
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from uuid import uuid5, NAMESPACE_DNS
from urllib.parse import urlparse

load_dotenv()

app = FastAPI()

# Get all the keys from the .env file
SEARCH_ENGINE_ID_BAGHAVEN = os.getenv("SEARCH_ENGINE_ID_BAGHAVEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
HTML_FETCH_TIMEOUT = 2

# fetch firebase credentials
print("Fetching firebase credentials...")
cred = credentials.Certificate("credentials/bag-haven-qt9s4v-firebase-adminsdk-h9x05-e584032402.json")
firebase_admin.initialize_app(cred)

# intialize firestore
print("Initializing firestore...")
db = firestore.client()
print("Initializing firestore done")

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to console
    ],
)

logger = logging.getLogger("Merchant Backend API")

class SearchRequest(BaseModel):
    query: str
    pages: int

# products class
class Product(BaseModel):
    productId: str
    id: str
    url: str
    title: str
    imageURL: str
    description: str
    price: float
    seller: str
    isOriginal: bool
    offerType: str
    priceCurrency: str
    timeCreated: datetime
    availability: str

"""
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- HELPER FUNCTIONS -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
"""

# save to firestore - not tested yet
def save_batch_to_firebase(data_list, collection_name="products"):
    batch = db.batch()
    collection_ref = db.collection(collection_name)
    
    for data in data_list:
        doc_ref = collection_ref.document()  # Auto-generate document ID
        batch.set(doc_ref, data)

    # Commit the batch
    try:
        batch.commit()
        print(f"Batch write completed with {len(data_list)} documents.")
    except Exception as e:
        print(f"Error in batch write: {e}")

# google vision image search
def search_image_google_vision(image_path, api_key):
    # Encode the image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "requests": [
            {
                "image": {"content": encoded_image},
                "features": [{"type": "WEB_DETECTION"}]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

# performs the google search
def perform_google_text_search(query, start):
    # this function performs the google search multiple times
    print(f"Starting at page {start}")
    try:
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID_BAGHAVEN,
            "q": query,
            "searchType": "image",
            "num": 10,
            "start": start
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        raw_search_results = data.get("items", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return raw_search_results


async def fetch_html_async(url, session):
    print(f"Fetching {url}...")
    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=HTML_FETCH_TIMEOUT) as response:
            print(f"Content-Type: {response.headers['Content-Type']}")
            response.raise_for_status()

            print(f"[SUCCESS] - Status code: {response.status} - {url}\n")
            responseText = await response.text()
            return {"url": url, "html": responseText}
    except Exception as e:
        
        # save these errors somewhere else -- just to check on why they are failing
        print(f"Error fetching {url}: {e}\n")
        return None

async def fetch_and_extract(urls):
    print("Fetching and extracting JSON-LD...")
    html_list = await fetch_all_html(urls)
    results = []

    # print(f"Results: {[(html['url'], len(html['html'])) for html in html_list if html]}\n\n")
    
    # create the product objects that you will send to the frontend
    for htmlObject in html_list:
        if htmlObject:

            # create the product object from the json ld and url
            url = htmlObject["url"]
            html = htmlObject["html"]
            json_ld = extract_json_ld(html, url)
            results.extend(json_ld)
    return results


async def fetch_all_html(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html_async(url, session) for url in urls]
        return await asyncio.gather(*tasks)

def get_seller_from_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def extract_json_ld(html, url):
    soup = BeautifulSoup(html, "html.parser")
    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)

            # # check if data is a list so that we only get lists of objects
            if isinstance(data, list):
                # get only the products in the array
                data = data[0]
            
            
            
            # we only care about Products and Organizations (TODO: Add Logic for Organizations)
            if data.get("@type", None) != "Product":
                print(f"Skipping {url} because it is not a product...")
                continue

            # get the seller
            seller = "Unknown Seller"

            if uid := data.get("@id", None):
                seller = get_seller_from_url(uid)

            # create a new product object
            product = Product(
                id=data.get("@id", None),
                productId=uuid5(NAMESPACE_DNS, data.get("@id", None)).hex,
                url=url,
                title=data.get("name", "No Title"),
                imageURL=data.get("image", [None])[0] if data.get("image") else "No Image URL",
                description=data.get("description", "No Description"),
                price=data.get("offers", {}).get("price", -1.0),
                seller=seller,
                isOriginal=data.get("isOriginal", False),
                offerType=data.get("offers", {}).get("@type", "Unknown Offer Type"),
                priceCurrency=data.get("offers", {}).get("priceCurrency", "USD"),
                timeCreated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                availability=data.get("offers", {}).get("availability", "Unknown Availability")
            )
            print("Created Product Object...")
            

            

            print(f"===Extracted JSON-LD for URL: {url}===\n")
            json_ld.append(product.__dict__)
            print("Extracted JSON-LD...")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing JSON-LD for {url}, Error Message: {e}\n")
            print("Skipping...")
            continue
    return json_ld


def extract_product_originization_info(json_ld):
    print("Extracting product originization info...")
    return json_ld

"""
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- API FUNCTION CALLS -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
"""

@app.get("/")
async def home():
    return {"message": "This is the home route"}


@app.post("/search/")
async def generic_search(request: SearchRequest):

    query = request.query
    pagesToQuery = request.pages

    # start time
    startTime = time.time()

    if pagesToQuery > 10:
        raise HTTPException(status_code=400, detail="Must query at Most 9 Pages")
    # final result that we send to the front end
    result = {}

    try:
        
        beforeSearchTime = time.time()

        # perform google search
        raw_search_results = perform_google_text_search(query, 1)

        # perform search the amount of pages
        for i in range(2, pagesToQuery+1):
            raw_search_results.extend(perform_google_text_search(query, (i*10)))
        
        # log search time taken
        print(f"Search Results Amount: {len(raw_search_results)}")
        print(f"Search Execution Time: {time.time() - beforeSearchTime:.2f} seconds")
        
        beforeHTMLTime = time.time()

        # we need to analyze the context links
        print("Analyzing Context Links...")
        urls = [result["image"]["contextLink"] for result in raw_search_results]

        extracted_data = await fetch_and_extract(urls)

        print(f"Extracted Data Amount: {len(extracted_data)}")

        extractedProductData = []

        for data in extracted_data:
            for item in data:
                extractedProductData.extend(item)
        

        print(f"HTML Execution Time: {time.time() - beforeHTMLTime:.2f} seconds")
        
        print(f"Raw Search Results Amount: {len(raw_search_results)}")

        timeTaken = time.time() - startTime
        print(f"Total Execution Time: {timeTaken:.2f} seconds")
        logger.info(f"Total Execution Time: {timeTaken:.2f} seconds")

        return {
            "query": query, 
            "extractedData": extracted_data, 
            "timeTaken": timeTaken,
            "extractedProductData": extractedProductData
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# search image google search 
@app.get("/googleVisionTest")
async def get_parse_image():
    
    imagePath = "test-images\image.png"
    GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

    # call the vision api
    resp = search_image_google_vision(imagePath, GOOGLE_VISION_API_KEY)
    
    # write the response to a json file using json dumps
    with open('response.json', 'w') as outfile:
        json.dump(resp, outfile)


    return {"message": "success"}