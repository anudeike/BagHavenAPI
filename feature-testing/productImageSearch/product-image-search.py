from google.cloud import vision_v1
from google.cloud.vision_v1 import ProductSearchClient
import os
import dotenv

# load environment variables
dotenv.load_dotenv()

# get credentials from the env file
GOOGLE_CLOUD_CREDENTIALS = os.getenv("GOOGLE_CLOUD_CREDENTIALS_PATH")
PROJECT_ID = "baghaven"

def create_product_set(
    project_id: str,
    location: str,
    product_set_id: str,
    product_set_display_name: str
):
    """
    Creates a Product Set in Google Cloud Vision Product Search.

    Args:
        project_id: GCP project ID.
        location: A valid GCP region that supports Product Search (e.g., "us-west1").
        product_set_id: A unique ID for your new Product Set.
        product_set_display_name: A human-readable name for your Product Set.
    """
    # Initialize the ProductSearchClient
    client = vision_v1.ProductSearchClient()

    # Build the parent resource name for the location
    location_path = f"projects/{project_id}/locations/{location}"

    # Construct the ProductSet object
    product_set = vision_v1.ProductSet(display_name=product_set_display_name)

    # Create the Product Set with the given ID
    response = client.create_product_set(
        parent=location_path,
        product_set=product_set,
        product_set_id=product_set_id
    )

    print(f"Product Set created: {response.name}")

if __name__ == "__main__":
    # Replace these values with your own
    PROJECT_ID = "baghaven"
    LOCATION = "us-west1"  # or another location that supports Product Search
    PRODUCT_SET_ID = "visualsearch-demo-product-set"
    PRODUCT_SET_DISPLAY_NAME = "visualsearch-demo-product-set"

    create_product_set(PROJECT_ID, LOCATION, PRODUCT_SET_ID, PRODUCT_SET_DISPLAY_NAME)
