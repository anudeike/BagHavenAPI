import csv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def export_products_to_csv(
    service_account_path: str,
    collection_name: str = "products",
    output_csv: str = "products.csv",
    product_set_id: str = "my_product_set_id",
    product_category: str = "general"
):
    """
    Exports all documents from a Firebase Firestore collection to a CSV file
    formatted for Google Cloud Vision Product Search bulk import.
    """

    # 1. Initialize Firebase Admin using your downloaded service account key
    cred = credentials.Certificate(service_account_path)

    # If you have multiple apps, you can optionally name this app. Otherwise, just do:
    firebase_admin.initialize_app(cred)

    # 2. Get Firestore client via Firebase Admin
    db = firestore.client()

    # 3. Define the CSV columns in the correct order
    csv_headers = [
        "image_uri",         # (1) image URI
        "image_id",          # (2) optional, can leave blank or set unique value
        "product_set_id",    # (3) product set ID in Product Search
        "product_id",        # (4) your internal product ID
        "product_category",  # (5) 'general', 'apparel', etc.
        "product_display_name",  # (6) optional
        "labels",            # (7) optional comma-delimited key=value pairs
        "bounding_poly"      # (8) optional
    ]

    # 4. Open the CSV file for writing
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        
        # Write the header row
        writer.writerow(csv_headers)

        # 5. Query the Firestore collection
        docs = db.collection(collection_name).limit(1000).stream()

        count = 0
        for doc in docs:
            data = doc.to_dict()
            
            # 6. Map Firestore fields to CSV columns

            # (1) image_uri: pick 'image' or 'baseImage' from your data
            image_uri = data.get("image") or data.get("baseImage") or ""

            # (2) image_id: optional. Using 'sku' or leave it blank
            image_id = data.get("sku", "")

            # (3) product_set_id: the ID of the product set you created in GCP
            ps_id = product_set_id

            # (4) product_id: from 'productId', or fallback to Firestore doc ID
            prod_id = data.get("productId", doc.id)

            # (5) product_category: 'general', 'apparel', etc.
            category = product_category

            # (6) product_display_name: 'name' or 'baseName'
            display_name = data.get("name") or data.get("baseName") or ""

            # (7) labels: e.g. "color=BLACK,size=2XL"
            color_label = f"color={data.get('color')}" if data.get("color") else ""
            size_label = f"size={data.get('size')}" if data.get("size") else ""
            
            label_parts = []
            if color_label:
                label_parts.append(color_label)
            if size_label:
                label_parts.append(size_label)
            
            labels = ",".join(label_parts)  # e.g. "color=BLACK,size=2XL"

            # (8) bounding_poly: leave blank unless you have bounding boxes
            bounding_poly = ""

            # Build the CSV row
            row = [
                image_uri,
                image_id,
                ps_id,
                prod_id,
                category,
                display_name,
                labels,
                bounding_poly
            ]
            
            writer.writerow(row)
            count += 1

        print(f"Exported {count} products to '{output_csv}' from Firestore.")

if __name__ == "__main__":
    # Path to your Firebase Admin service account JSON file
    SERVICE_ACCOUNT_PATH = "credentials/bag-haven-qt9s4v-firebase-adminsdk-h9x05-e584032402.json"

    export_products_to_csv(
        service_account_path=SERVICE_ACCOUNT_PATH,
        collection_name="products",        # your Firestore collection
        output_csv="all_firebase_products.csv",         # output CSV filename
        product_set_id="visualsearch-demo-product-set",# must match your GCP product set ID
        product_category="general"         # or 'general', 'homegoods', etc.
    )
