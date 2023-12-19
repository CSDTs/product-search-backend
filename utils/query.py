from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import os
from dotenv import load_dotenv
from utils.af_neo4j import App
import pandas as pd

load_dotenv()

NEO4J_CONFIG = {
    'uri': os.environ.get('CSDT_GRAPH_URI'),
    'database':'neo4j',
    'auth': {'user': os.environ.get('CSDT_USER'), 'pwd': os.environ.get('CSDT_PASSWORD')}
}

MODEL = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2')

class Query(ABC):
    @property
    def text(self):
        return self._text

    @property
    def database(self):
        return self._database

    @abstractmethod
    def method(self):
        pass

    # optional
    def context(self):
        pass

class RetreiveRerankQuery(Query):
    def __init__(self, retriever):
        self._text = None
        self._database = None
        self.model = MODEL
        self.retriever = retriever

    @property
    def database(self):
        return self._database

    @database.getter
    def database(self):
        # todo: if < X seconds, else re-fetch?
        if self._database is None:
            self._database = self.retriever()
        return self._database

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @text.getter
    def text(self):
        return self._text

    def method(self):
        scores = self.model.predict([
            (self.text, product) for product in self.database
        ])
        return scores

class Retriever(ABC):
    @property
    def content_data(self):
        return self._content_data

    @property
    def uri_data(self):
        return self._uri_data

    @content_data.getter
    def content_data(self):
        return self._content_data

    @uri_data.getter
    def uri_data(self):
        return self._uri_data

class ArtisanNeo4jRetriever(Retriever):
    def __init__(self):
        app = App()
        HAS_URL = "HAS_URL"
        HAS_IMG = "HAS_IMG"
        CONTENT = ["Materials", "Principles", "Processes"]
        PRINCIPLES = "Principles"
        THE_ARTISAN = "MADE"
        THE_CRAFT = "INSTANCE_OF"
        wide_column_names = [
            "product", "content", "principles", "the_artisan", "url", "image", "craftID"
        ]

        #cypher = "MATCH (c:CraftID)-[r:INSTANCE_OF|:Product|Materials|:Processes|:Principles|:HAS_URL|:HAS_IMG|:MADE]-(n) RETURN c,type(r),n"
        cypher = "MATCH (c:CraftID)-[r:INSTANCE_OF|Product|Materials|Processes|Principles|HAS_URL|HAS_IMG|MADE]-(n) RETURN c, type(r), n"
       
        _raw_database = [record.values() for record in app.query_database(cypher)]

        df = pd.DataFrame(
            columns = ["craftID", "relationship", "value"],
            data =\
                [
                    (
                        list(item[0].values())[0],
                        item[1], 
                        list(item[2].values())[0]
                    ) 
                    for item in _raw_database
                ]
        )

        tall_df = pd.DataFrame(
            columns = ["craftID", "relationship", "value"],
            data =\
                [
                    (
                        list(item[0].values())[0],
                        item[1], 
                        list(item[2].values())[0]
                    ) 
                    for item in _raw_database
                ]
        )

        wide_data = []
        for craftid, craftid_df in tall_df.groupby('craftID'):
            principles_processes_materials = " ".join(
            craftid_df.query(
                    'relationship in @CONTENT'
                )['value'].values)
            principles = ",".join(
                craftid_df.query(
                    'relationship == @PRINCIPLES'
                )['value'].values)
            url = craftid_df.query(
                'relationship == @HAS_URL'
                ).values[0][-1]
            image = craftid_df.query(
                'relationship == @HAS_IMG'
                ).values[0][-1]                
            artisan = craftid_df.query(
                'relationship == @THE_ARTISAN'
                ).values[0][-1]
            the_craft = craftid_df.query(
                'relationship == @THE_CRAFT'
                ).values[0][-1]
            wide_data.append(
                (the_craft, principles_processes_materials, principles, artisan, url, image, craftid)
            )

        self.wide_df = pd.DataFrame(
            wide_data, 
            columns=wide_column_names
        )

        self._content_data = self.wide_df.content.values
        self._uri_data = self.wide_df.url.values

    def _get_content(self):
        return self.app.query_database(self.cypher)
    
    def retriever(self):
        return self.content_data
    
    def get_artisans(self):
        return self.wide_df.the_artisan.values

    def get_principles(self):
        return self.wide_df.the_artisan.values