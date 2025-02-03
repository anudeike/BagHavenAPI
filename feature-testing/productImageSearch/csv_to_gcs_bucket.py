import os
import requests
import pandas as pd
from google.cloud import storage
from uuid import uuid4

# Global configuration
BUCKET_NAME = "demo-product-seekeasy-images"
INPUT_CSV = "top1000_firebase_products.csv"
OUTPUT_CSV = "updated_demo_product_images.csv"

def get_gcs_client():
    """Initialize and return a Google Cloud Storage client."""
    return storage.Client()

def upload_image_to_gcs(image_url: str, bucket_name: str, blob_name: str) -> str:
    """
    Fetches an image from `image_url` and uploads it to the specified GCS bucket.
    Returns the public GCS URL of the uploaded object.
    """
    storage_client = get_gcs_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    # Download image from the URL
    response = requests.get(image_url, stream=True, headers=headers)
    response.raise_for_status()  # raise an exception if the download failed

    # Upload the content to GCS
    # You could also detect or explicitly set a more accurate content type if desired
    blob.upload_from_string(
        response.content,
        content_type=response.headers.get('Content-Type', 'application/octet-stream')
    )

    return blob.public_url

def main():
    # Read the CSV as a pandas DataFrame
    df = pd.read_csv(INPUT_CSV)

    # Create a new column `website_image_link` to hold the original URLs
    df["website_image_link"] = df["image_uri"]

    # Function to process a single image link
    def process_image_url(image_url):
        # Derive a filename from the URL
        file_name = os.path.basename(image_url)
        if not file_name:
            # Fallback if no basename is found
            # needs to be unique
            file_name = f"uploaded_image_{uuid4().hex[:5]}.jpg"
        
        # Upload the image and return the GCS URL
        new_url = upload_image_to_gcs(image_url, BUCKET_NAME, file_name)
        return new_url

    # Apply the upload process to each row in `image_uri`
    df["image_uri"] = df["image_uri"].apply(process_image_url)

    # Save the updated DataFrame to a new CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Finished! The updated CSV has been written to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
