from google.cloud import vision_v1

def import_product_sets(project_id, location, gcs_source_uri, product_set_id):
    product_search_client = vision_v1.ProductSearchClient()

    parent = f"projects/{project_id}/locations/{location}"

    gcs_source = vision_v1.ImportProductSetsGcsSource(
        csv_file_uri=gcs_source_uri

    )
    input_config = vision_v1.ImportProductSetsInputConfig(
        gcs_source=gcs_source
    )

    operation = product_search_client.import_product_sets(
        parent=parent,
        input_config=input_config
    )

    print("Processing import... this may take a while.")
    result = operation.result()  # Wait for the operation to complete

    # Check for errors or success
    for i, status in enumerate(result.statuses):
        if status.code != 0:
            print(f"Error on index {i}: {status.message}")
        else:
            print(f"Imported product set: {status.reference_images}")

# Example usage
import_product_sets(
    project_id="baghaven",
    location="us-west1",
    gcs_source_uri="gs://demo-products-bkt/updated_demo_product_images-noweblink.csv",
    product_set_id="visualsearch-demo-product-set"
)
