import io
from google.cloud import vision

def search_similar_products(
    project_id: str,
    location: str,
    product_set_id: str,
    product_category: str,
    image_path: str,
    max_results = 10
):
    """
    Searches for similar products using the local image at `image_path`.
    If your image is stored in GCS, you can modify the code accordingly.
    """

    # Initialize the clients
    product_search_client = vision.ProductSearchClient()
    image_annotator_client = vision.ImageAnnotatorClient()

    # Read the local image file
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    # Create annotate image request along with product search feature.
    image = vision.Image(content=content)

    # product search specific parameters
    product_set_path = product_search_client.product_set_path(
        project=project_id, location=location, product_set=product_set_id
    )

    product_search_params = vision.ProductSearchParams(
        product_set=product_set_path,
        product_categories=[product_category]
    )

    image_context = vision.ImageContext(product_search_params=product_search_params)

    # Search products similar to the image.
    response = image_annotator_client.product_search(
        image, image_context=image_context, max_results=max_results
    )

    index_time = response.product_search_results.index_time
    print("Product set index time: ")
    print(index_time)

    results = response.product_search_results.results

    print("Search results:")
    for result in results:
        product = result.product

        print(f"Score(Confidence): {result.score}")
        print(f"Image name: {result.image}")

        print(f"Product name: {product.name}")
        print("Product display name: {}".format(product.display_name))
        print(f"Product description: {product.description}\n")
        print(f"Product labels: {product.product_labels}\n")

def main():
    # Adjust these values
    project_id = "baghaven"
    location = "us-west1"
    product_set_id = "visualsearch-demo-product-set"
    product_category = "apparel"  # or "homegoods-v2", "toys-v2", etc.

    # Provide a path to an image you want to test
    # (This could also be a GCS URI. For local file, read its bytes as shown above.)
    test_image_path = "feature-testing/productImageSearch/test_image.jpg"

    search_similar_products(
        project_id=project_id,
        location=location,
        product_set_id=product_set_id,
        product_category=product_category,
        image_path=test_image_path
    )

if __name__ == "__main__":
    main()
