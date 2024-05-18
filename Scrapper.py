from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.safari.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from requests.exceptions import HTTPError, RequestException

import os
import time
import csv
import requests


def create_product_dir(product_name):
    dir_path = os.path.join(os.getcwd(), product_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def download_image(image_url, path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            f.write(response.content)


def download_document_with_retry(doc_url, save_path, max_retries=5):
    retry_wait = 1  # Start with 1 second wait time
    for attempt in range(max_retries):
        try:
            with requests.get(doc_url, stream=True) as response:
                response.raise_for_status()  # Raises HTTPError for bad responses
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return save_path
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except RequestException as req_err:
            print(f"Connection error occurred: {req_err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        print(f"Retrying in {retry_wait} seconds...")
        time.sleep(retry_wait)
        retry_wait *= 2  # Exponential backoff

    print(f"Failed to download document after {max_retries} attempts.")
    return None


# Read links
products = []
with open('product_details.csv', 'r', encoding='utf-8') as file:  # Replace path to the csv file we got
    reader = csv.reader(file)
    next(reader)  # Skip the header
    for row in reader:
        products.append(row)

print(f"Total products: {len(products)}")

# Navigate to each product
driver = webdriver.Safari()
wait = WebDriverWait(driver, 10)

for product_name, product_link in products:
    # Navigate to each product link
    driver.get(product_link)
    time.sleep(15)  # Allow page to load
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'ti-tab-container')))

    table_view_more = driver.find_element(By.TAG_NAME, 'ti-view-more')
    rows = table_view_more.find_elements(By.TAG_NAME, 'ti-multicolumn-list-row')

    path = create_product_dir(product_name)
    file_path = os.path.join(path, 'product_details.txt')

    # Write product details
    with open(file_path, 'w', encoding='utf-8') as file:
        # Write the first part
        table_view_more = driver.find_element(By.TAG_NAME, 'ti-view-more')
        rows = table_view_more.find_elements(By.TAG_NAME, 'ti-multicolumn-list-row')
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'ti-multicolumn-list-cell')
            cell_texts = [cell.find_element(By.TAG_NAME, 'span').text for cell in cells]
            file.write(' '.join(cell_texts) + '\n')

        # Write a separator (optional)
        file.write('\n')

        # Write the second part
        try:
            features_tab_panel = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ti-tab-panel[tab-title='Features']")))
            view_more = features_tab_panel.find_element(By.TAG_NAME, "ti-view-more")
            list_items = view_more.find_elements(By.CSS_SELECTOR, 'ul > li')
            for item in list_items:
                file.write(item.text + '\n')
        except TimeoutException:
            print("No 'Features' tab found for this product.")

        file.write('\n')

        try:
            des_view_more = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ti-tab-panel[tab-title='Description']")))
            more = des_view_more.find_element(By.TAG_NAME, "ti-view-more")

            descriptions = more.find_elements(By.CSS_SELECTOR, 'p')
            for description in descriptions:
                file.write(description.text + '\n')
        except TimeoutException:
            print("No 'Description' tab found for this product.")

    # Download Images
    media_gallery = driver.find_element(By.CSS_SELECTOR, 'ti-media-gallery')
    images = media_gallery.find_elements(By.CSS_SELECTOR, 'ti-image')

    for index, image in enumerate(images):
        image_url = image.get_attribute('src')
        # Remove ':small' from the URL if present
        if image_url.endswith(':small'):
            image_url = image_url[:-6]  # Remove the last 6 characters ':small'

        # Construct the full image URL if it's a relative URL
        if image_url.startswith('/'):
            image_url = 'https://ti.com' + image_url  # Replace with the actual base URL

        # Define the filename with the index to avoid overwriting and extract the file extension from the URL
        file_extension = image_url.split('.')[-1].split('?')[0]  # Ignore query params for file extension
        filename = f'image_{index}.{file_extension}'
        file_path = os.path.join(path, filename)
        # Download and save the image
        download_image(image_url, file_path)

    # Download files
    techdocs = driver.find_element(By.CSS_SELECTOR, 'ti-techdocs')
    doc_links = techdocs.find_elements(By.CSS_SELECTOR, 'tbody tr td a:first-child')

    # Loop through each link, download and save the document
    for index, doc_link in enumerate(doc_links):
        doc_url = doc_link.get_attribute('href')

        # Check if the URL is valid
        if doc_url:
            # Define the filename using the last part of the URL to avoid overwriting
            filename = doc_url.split('/')[-1] + '.pdf'
            save_path = os.path.join(path, filename)

            # Download and save the document
            try:
                download_document_with_retry(doc_url, save_path)
            except Exception as e:
                print(f"Failed to process {product_name}, error: {e}")
    print(product_name)

driver.quit()