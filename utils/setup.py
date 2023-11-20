from utils.patterns import AbstractDockerState
from utils.af_neo4j import App, stage_database_write
import docker
from docker import errors
import pandas as pd
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

CSDT_NEO4j = os.environ.get("CSDT_CONTAINER")
AF_ROW_OF_DATA =\
    {
        'artisan': None,
        'product name': None,
        'principles': None,
        'materials': None,
        'processes': None,
        'industrial scale items': None,
        'url': None,
        'image': None
    }

class StubDockerState(AbstractDockerState):
    @staticmethod
    def _check(): True
    @staticmethod
    def _start_or_run_neo4j(): True
    @staticmethod
    def _upload_data_to_neo4j(): True
    @staticmethod
    def _check_neo4j_db(): True
    @staticmethod
    def _shutdown_neo4j_db(): True

class DockerState(AbstractDockerState):
    container_name = 'neo4j'

    @staticmethod
    def _check(timeout=20):
        response = False

        client = docker.APIClient(timeout=timeout)
        try:
            client.ping()
            response = True
        except errors.APIError:
            pass

        client.close()
        return response

    @staticmethod
    def _start_or_run_neo4j(container_name=CSDT_NEO4j, timeout=20):
        need_to_run_container = False
        need_to_start_container = False
        # check if container exists, otherwise create it. Then start it
        client = docker.from_env(timeout=timeout)
        try:
            csdt_neo4j = client.containers.get(container_name)
            need_to_start_container = True # found container
        except errors.NotFound: # .get() raises
            need_to_run_container = True

        if need_to_run_container:
            response = subprocess.check_call('./neo4j.sh', shell=True) # to pass .env

        if need_to_start_container and csdt_neo4j.status != "running":
            csdt_neo4j.start()
            client.close() # refresh client
            csdt_neo4j = client.containers.get(container_name)

        return csdt_neo4j.status == 'running'

    @staticmethod
    def _upload_data_to_neo4j(csv_filename):
        df = pd.read_csv(csv_filename)
        stage_database_write(df)
        return True

    @staticmethod
    def _check_neo4j_db(what="Artisan"):
        app = App()
        the_result = app.check_database(what=what)
        app.close()
        return the_result

    @staticmethod
    def _query_database(query=None):
        the_result = None
        if query is not None:
            app = App()
            the_result = app.query_database(cypher=query)
            app.close()
        return the_result        

    @staticmethod
    def _shutdown_neo4j_db(container_name=CSDT_NEO4j, timeout=20):
        response = True
        client = docker.from_env(timeout=timeout)
        csdt_neo4j = client.containers.get(container_name)
        csdt_neo4j.stop()

        client.close() # refresh client
        csdt_neo4j = client.containers.get(container_name)

        return csdt_neo4j.status == 'exited'

# note: Ideally we should make an Abstract Factory for Database
# that contains write, read, delete, and setup 
# that is implemented by App and DockerState functions. There's
# some cruft developing here


def add_from_squarespace(url: str=None, 
                         db_writer: callable=None, url_getter: callable=None):
    def _yield_af_data_from_squarespace(url):
        df = None
        the_json = url_getter(url)

        the_base_url = the_json['website']['baseUrl']
        for an_item in the_json['items']:
            yield {
                'artisan': the_json['website']['siteTitle'].strip(),
                'product name': an_item['title'].strip(),
                'url': '/'.join([
                        the_base_url,
                        an_item['fullUrl']
                    ]).strip(),
                'principles': '',
                'processes': '',
                'image': an_item['assetUrl'].strip(),
                'materials': ", ".join(an_item['categories']).strip(),
                'industrial scale items': ''
            }

    df = pd.DataFrame(
        data =\
            _yield_af_data_from_squarespace(url)
    )

    if df is not None and db_writer is not None:
        db_writer(df)

    return df