from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import base64
import json
from bs4 import BeautifulSoup
import json

load_dotenv()

app = FastAPI()

# Get all the keys from the .env file
SEARCH_ENGINE_ID_BAGHAVEN = os.getenv("SEARCH_ENGINE_ID_BAGHAVEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

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

# search image google search 

@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}

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

@app.get("/")
async def home():
    return {"message": "This is the home route"}

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

def fetch_html(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_json_ld(html):
    soup = BeautifulSoup(html, "html.parser")
    json_ld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            json_ld.append(data)
            print("Extracted JSON-LD: ", data)
        except (json.JSONDecodeError, TypeError):
            continue
    return json_ld


@app.post("/search/")
async def generic_search(request: SearchRequest):

    query = request.query
    pagesToQuery = request.pages

    if pagesToQuery > 10:
        raise HTTPException(status_code=400, detail="Must query at Most 9 Pages")
    # final result that we send to the front end
    result = {}

    try:
        raw_search_results = perform_search(query, 1)

        # perform search the amount of pages
        for i in range(2, pagesToQuery+1):
            raw_search_results.extend(perform_search(query, (i*10)))
        
        print(f"Search Results Amount: {len(raw_search_results)}")

        # filter the search results by products only
        productResults = []
        for result in raw_search_results:
            if result["pagemap"].get("metatags") is not None:
                for metatag in result["pagemap"]["metatags"]:
                    if metatag.get("og:type") == "product":
                        productResults.append(result)

        # get the html of each product
        for product in productResults:
            productHtml = fetch_html(product["link"])
            product["json_ld"] = extract_json_ld(productHtml)
        
        print(f"Product Search Results Amount: {len(productResults)}")


        return {"query": query, "results": productResults}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))