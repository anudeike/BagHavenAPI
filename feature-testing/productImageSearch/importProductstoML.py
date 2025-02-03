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

    # result if of type: ImportProductSetsResponse 
    # attributes: reference_images, statuses

    # Check for errors or success
    for i, res in enumerate(zip(result.reference_images, result.statuses)):
        if res[1].code != 0:
            print(f"Error on index {i}: {res[1].message}")
        else:
            # Success
            print(f"Imported product {i} - product name: {res[0].name}, image uri: {res[0].uri}")
            

GS_BUCKET_FILE_NAME = "demo-products-bkt/demo_product_files_noheader.csv"

# Example usage
import_product_sets(
    project_id="baghaven",
    location="us-west1",
    gcs_source_uri=f"gs://{GS_BUCKET_FILE_NAME}",
    product_set_id="visualsearch-demo-product-set"
)
