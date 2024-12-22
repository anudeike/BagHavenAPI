from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

# Use an API key with `listIndexes` ACL
client = SearchClient.create(os.getenv("ALGOLIA_APP_ID"), os.getenv("ALGOLIA_API_KEY"))
indices = client.list_indices()["items"]

print(indices)