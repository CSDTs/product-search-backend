# Product Search

The product search repository implements searching for products from Artisanal Futures members that are already stored in a Neo4j database. Design patterns were used in the form of abstract classes to make the code flexible enough to accomadate revisions and other needs.

This code base originally used a GUI, using streamlit, but now only offers an API for searching.

## Getting started

### Quick Versiom
```bash
./run.sh
```

### API Swagger Documentation
* Start API
* see: [localhost search endpoint](http://127.0.0.1:8000/docs#/default/search_search__post)

## Detailed Version

### AF Database container setup 
tl;dr version: `./utils/neo4j.sh`

```bash
docker run \
    --name csdt_neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
     --env NEO4J_AUTH=${CSDT_USER}/${CSDT_PASSWORD} \
     neo4j:3.5.3 \
     || \
# or just start the container if already exists
echo '... starting container csdt_neo4j ...' && docker start csdt_neo4j
```

### Product Search API container setup
```bash
docker build -t product-search-api -f Dockerfile.web .
```

### Product Search API service
```bash
docker compose up # wait a minute or so
# note: if you do not have the compose plugin form, (see here)[https://docs.docker.com/compose/install/linux/#install-using-the-repository]
# go to http://<host of the container>/docs#/default/upload_new_database_upload_new_database__post, click Try it! and upload a .csv
# you can use data/artisanal futures database  - Sheet1 - 6-27-2022.csv for default data.
```

### Add default or a specifc database to Product Serach
```
# go to https://localhost:80/docs/upload_new_data
# On the swagger UI, click "Try it!"
# If you want to upload default data (stored in github) then skip selecting a .csv file.
# If you want to select a .csv file, click on the Upload button to select it
# Click Submit
# You can verify data is uploaded by going to https://localhost:7474/ and inspecting the database
```



## Older instructions (ignore)
### Python Setup
```bash
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Launch the API
```bash
uvicorn api:app --reload
# Partially complete python GIU
#streamlit run search_gui.py
# go to ... http://127.0.0.1:8000/docs#/ to play with the swagger spec, work with the API
```

### Run unit and integration tests

Note the integration test assumes a clean Neo4j instance with data pushed from `./data/artisanal futures database  - Sheet1.csv`
```bash
pytest test
```