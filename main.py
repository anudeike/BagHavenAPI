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

load_dotenv()

app = FastAPI()

# Get all the keys from the .env file
SEARCH_ENGINE_ID_BAGHAVEN = os.getenv("SEARCH_ENGINE_ID_BAGHAVEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

# fetch firebase credentials
print("Fetching firebase credentials...")
cred = credentials.Certificate("credentials/bag-haven-qt9s4v-firebase-adminsdk-h9x05-e584032402.json")
firebase_admin.initialize_app(cred)

# intialize firestore
print("Initializing firestore...")
db = firestore.client()
print("Initializing firestore done")

class SearchRequest(BaseModel):
    query: str
    pages: int


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
def perform_search(query, start):
    # this function performs the google search multiple times
    print(f"Starting at page {start}")
    try:
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID_BAGHAVEN,
            "q": query,
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
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        
        # save these errors somewhere else -- just to check on why they are failing
        print(f"Error fetching {url}: {e}")
        return None

async def fetch_and_extract(urls):
    print("Fetching and extracting JSON-LD...")
    html_list = await fetch_all_html(urls)
    results = []
    for html in html_list:
        if html:
            json_ld = extract_json_ld(html)
            results.append(json_ld)
    return results


async def fetch_all_html(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html_async(url, session) for url in urls]
        return await asyncio.gather(*tasks)


def extract_json_ld(html):
    soup = BeautifulSoup(html, "html.parser")
    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            json_ld.append(data)
            print("Extracted JSON-LD...")
        except (json.JSONDecodeError, TypeError):
            continue
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
        raw_search_results = perform_search(query, 1)
        

        # perform search the amount of pages
        for i in range(2, pagesToQuery+1):
            raw_search_results.extend(perform_search(query, (i*10)))
        
        print(f"Search Results Amount: {len(raw_search_results)}")

        print(f"Search Execution Time: {time.time() - beforeSearchTime:.2f} seconds")

        # filter the search results by products only
        productResults = []
        for result in raw_search_results:
            if result["pagemap"].get("metatags") is not None:
                for metatag in result["pagemap"]["metatags"]:
                    if metatag.get("og:type") == "product":
                        productResults.append(result)
        
        beforeHTMLTime = time.time()

        # get the url
        urls = [result["link"] for result in raw_search_results]

        extracted_data = await fetch_and_extract(urls)

        print(len(extracted_data))

        print(f"HTML Execution Time: {time.time() - beforeHTMLTime:.2f} seconds")
        
        print(f"Raw Search Results Amount: {len(raw_search_results)}")
        print(f"Product Search Results Amount: {len(productResults)}")

        timeTaken = time.time() - startTime
        print(f"Total Execution Time: {timeTaken:.2f} seconds")

        return {"query": query, "results": raw_search_results, "productResults": productResults, "extractedData": extracted_data, "timeTaken": timeTaken}
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