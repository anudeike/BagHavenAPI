import pandas as pd

FILE_PATH = "updated_demo_product_images-noweblink.csv"
BUCKET_NAME = "demo-product-seekeasy-images"
OUTPUT_FILE_PATH = "updated_demo_product_images_noweblink_gsutil.csv"

def transfrom_image_uri(image_uri):

    image_name = image_uri.split("/")[-1]
    return f"gs://{BUCKET_NAME}/{image_name}"

def clean_labels(label_str):
    if not isinstance(label_str, str):
        return ""  # or return None if there's no label string
    # Remove trailing or leading commas/spaces
    cleaned = label_str.strip().strip(",")

    # Remove any spaces
    cleaned = cleaned.replace(" ", "")
    return cleaned


"""
gs://[BUCKET_NAME]/[OBJECT_NAME]
Error on index 825: Invalid GCS path specified: 

https://storage.googleapis.com/demo-product-seekeasy-images/15231834_hi

example: gs://demo-product-seekeasy-images/11552290_hi
"""

df = pd.read_csv(FILE_PATH)

#df["image_uri"] = df["image_uri"].apply(transfrom_image_uri)

df["labels"] = df["labels"].apply(clean_labels)

# print(df.head(3))
df.to_csv(OUTPUT_FILE_PATH, index=False)

