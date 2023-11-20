#!/bin/sh
docker run \
    --name csdt_neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
     --env NEO4J_AUTH=${CSDT_USER}/${CSDT_PASSWORD} \
     neo4j:3.5.3
