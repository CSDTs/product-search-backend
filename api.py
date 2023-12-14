import pandas as pd
import json
import httpx
import requests

from utils.query import ArtisanNeo4jRetriever
from utils.query import RetreiveRerankQuery
from utils.af_neo4j import write_to_graph_db
from utils.setup import add_from_squarespace
from pydoc import describe
from typing import List
from io import StringIO
from fastapi import FastAPI, File, UploadFile,  Response
from pydantic import BaseModel
from bs4 import BeautifulSoup
from bs4.element import Tag

class ArrayIndicesViewer:
    @staticmethod
    def reindex(the_array, the_indices):
        return the_array[the_indices]

    @staticmethod
    def ranking(the_array):
        sorted_array = sorted(the_array)
        return [
            sorted_array.index(
                a_ranking
            ) for a_ranking in the_array
        ]

class ProductSearchController:
    def __init__(self, model=None, view=None, array_viewer=None):
        self.model = model() # we need its retriewer
        self.view = view(self.model.retriever) # ... to a view of the db at time of call
        self.array_viewer = array_viewer()

    def _search(self, text):
        self.view.text = text
        ranking = self.view.method()
        return self.array_viewer.ranking(ranking)

    def search(self, text):
        ranking = self._search(text)
        return self.model.wide_df.loc[ranking].reset_index(drop=True)

prod = ProductSearchController(
    ArtisanNeo4jRetriever,
    RetreiveRerankQuery,
    ArrayIndicesViewer
)

default_image = "https://cdn1.vectorstock.com/i/thumb-large/46/50/missing-picture-page-for-website-design-or-mobile-vector-27814650.jpg"

class Craft(BaseModel):
    name: str
    description: str
    principles: str
    the_artisan: str
    url: str
    image: str = default_image # url
    craftID: str

class Search(BaseModel):
    content: str

def a_result_viewer(a_result, key):
    column_map = {
        "product": "product",
        "content": "content",
        "principles": "principles",
        "the_artisan": "the_artisan",
        "url": "url",
        "image": "image" ,
        "craftID": "craftID"
    }
    response = ""

    lookup = column_map[key]
    if lookup in a_result:
        response = a_result[lookup]
    return response

def results_viewer(results):
    return [a_result for _, a_result in results.iterrows()]

app = FastAPI()

@app.post("/search/")
async def search(query: Search, response_model: List[Craft]):    
    response = []
    for a_result in results_viewer(prod.search(query.content)):
        response.append(
            Craft(
                name=a_result_viewer(a_result,'product'),
                description=a_result_viewer(a_result,'content'),
                principles=a_result_viewer(a_result,'principles'),
                the_artisan=a_result_viewer(a_result,'the_artisan'),
                url=a_result_viewer(a_result,'url'),
                image=a_result_viewer(a_result,'image'),
                craftID=a_result_viewer(a_result,'craftID')
            )
        )

    print(response)

    return response

@app.post("/upload_new_database/")
async def upload_new_database(the_upload_file: UploadFile, 
                              add_dabls_website: str="o"):
    add_dabls_website = add_dabls_website
    df = pd.read_csv(the_upload_file.file)
    write_to_graph_db(df)

    print("\t wrote .csv file to database ...")

    print(f"\t trying to fetch squarespace related data {add_dabls_website} ...")
    if add_dabls_website is not None and add_dabls_website != '':
        url_getter = lambda x: requests.get(x).json()
        db_writer = write_to_graph_db
        add_from_squarespace(
            add_dabls_website,
            url_getter = url_getter,
            db_writer = write_to_graph_db
        )
        print("\t wrote square space data to database ...")

    return


##
## scrapping the olive mode e-commerce website
##
async def scrape_page(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        ##
        ## Get all products div
        ##
        products = soup.find_all("li", class_="grid__item scroll-trigger animate--slide-in")

        scraped_data = []
        for product in products:
            product_title = product.find("h3").text.strip()
            regular_price = product.find("span", class_="visually-hidden visually-hidden--inline").text.strip()
            regular_price_item = product.find("span", class_="price-item price-item--regular").text.strip()
            last_price = product.find("span", class_="price-item price-item--sale price-item--last").text.strip().replace("From ", "")
            unit_price = product.find("span", class_="visually-hidden").text.strip().replace("From ", "")
            url = "https://www.olivemodeboutique.com" + product.find("a")["href"]

            ##
            ## Remove the // from the image URL
            ##
            product_image_url = product.find("img")["src"].replace("//", "")

            ##
            ## Append the data to the list
            ##
            scraped_data.append({
                "artisan": "olive mode",
                "product name": product_title,
                "principles": "woman owned, black owned",
                "materials": "",
                "processes": "",
                "industrial scale items": "",
                "regular price": regular_price,
                "regular price item": regular_price_item,
                "last price": last_price,
                "unit price": unit_price,
                "image": product_image_url,
                "url": url
            })

        return scraped_data
    else:
        return []
    

##
## handling pagnation
##

async def scrape_olive_mode_shopify_with_pagination():
    base_url = "https://www.olivemodeboutique.com/collections/all"
    page_number = 1
    all_scraped_data = []

    while True:
        url = f"{base_url}?page={page_number}"

        ##
        ## Scrape the current page
        ##
        scraped_data = await scrape_page(url)

        ##
        ## If no data is found on the current page, break out of the loop
        ##
        if not scraped_data:
            break

        ##
        ## Add the scraped data to the overall list
        ##
        all_scraped_data.extend(scraped_data)

        ##
        ## Move to the next page
        ##
        page_number += 1
    ##
    ## Create a DataFrame with all scraped data
    ##
    df = pd.DataFrame(all_scraped_data)

    ##
    ## Generate CSV file
    ##
    csv_filename = "olive_mode_scraped_data.csv"
    df.to_csv(csv_filename, index=False, encoding="utf-8")

    return {"data": all_scraped_data, "csv_filename": csv_filename}

@app.get("/v2/products/olivemode")
async def scrape_data():
    result = await scrape_olive_mode_shopify_with_pagination()
    return result
 

##
## Dabls Mbad African bead museum
##

async def scrape_dabls_mbad():
    url = "https://www.mbad.org/"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        ##
        ## Get all products div
        ##
        products = soup.find_all("div", class_="product-overlay")

        ##
        ## Get the images div
        ##
        images = soup.find_all("div", class_="product-image sqs-pinterest-image")

        product_link = soup.find_all("div", class_="clear sqs-pinterest-products-wrapper")

        scrapped_data = []
        for product, image_url in zip(products, images):
            product_title = product.find("div", class_="product-title").text.strip()
            product_price = product.find("div", class_="product-price").text.strip().replace("Sale Price ", "")
            image_url = image_url.find("img")["data-image"]
            # product_url = "https://www.mbad.org" + product_link.find("a")["href"]   ##image URL still not working

            ##
            ## Append the data to the list
            ##
            scrapped_data.append({
                "artisan": "Dabls Mbad African Bead Museum",
                "product name": product_title,
                "principles": "african american civil rights, african culture, african american culture",
                "materials": "",
                "processes": "",
                "industrial scale items": "",
                "regular price": product_price,
                "image": image_url,
                "url": "",
            })
        ##
        ## Create a DataFrame with scraped data
        ##
        df = pd.DataFrame(scrapped_data)

        ##
        ## Generate CSV file
        ##
        csv_filename = "mbad_scraped_data_dabls_african_museum.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8")

        return {"data": scrapped_data, "csv_filename": csv_filename}
    else:
        return {"error": f"Failed to fetch data. Status code: {response.status_code}"}

@app.get("/v2/products/mbad")
async def scrape_data():
    result = await scrape_dabls_mbad()
    return result



##
## scrapping funky phils website: code not working
##
async def scrape_funkyphil_store():
    url = "https://funkyphil.com/products-page"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        ##
        ## Get all products div
        ##
        products = soup.find_all("div", class_="productcol")

        ##
        ## Get the images div
        ##
        # images = soup.find_all("div", class_="wrap wpsc_container")

        scrapped_data = []
        for product in zip(products):
            product_title = product.find("h3", class_="wpsc_product_title").text.strip()
            product_price = product.find("div", class_="wpsc_product_price2").text.strip().replace("Price:", "")
            url = product.find("img")["src"]
            print(products)
            ##
            ## Append the data to the list
            ##
            scrapped_data.append({
                
                "Product Title": product_title,
                "Regular Price": product_price,
                "Product Image URL": url
            })
        ##
        ## Create a DataFrame with scraped data
        ##
        df = pd.DataFrame(scrapped_data)

        ##
        ## Generate CSV file
        ##
        csv_filename = "scraped_data_dabls_funky_phil_store.csv"
        df.to_csv(csv_filename, index=False, encoding="utf-8")

        return {"data": scrapped_data, "csv_filename": csv_filename}
    else:
        return {"error": f"Failed to fetch data. Status code: {response.status_code}"}

@app.get("/v2/products/funkyphil")
async def scrape_data():
    result = await scrape_funkyphil_store()
    return result