from utils.query import ArtisanNeo4jRetriever
from utils.query import RetreiveRerankQuery
from utils.af_neo4j import write_to_graph_db
from utils.setup import add_from_squarespace
from pydoc import describe
from typing import List
from io import StringIO
import pandas as pd
import requests
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

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
                              add_dabls_website: str="https://www.mbad.org/beadstore/?format=json"):
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
