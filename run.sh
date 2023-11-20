#!/bin/sh
echo '... starting Neo4j container'
./utils/neo4j.sh;
echo '... activating virtual environment ....'
source ./venv/bin/activate
echo '... installing requirements.txt ....'
pip install -r requirements.txt
echo '... launching product search API'
uvicorn api:app --reload
#streamlit run search_gui.py