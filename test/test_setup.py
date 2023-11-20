import pytest
import json
from utils.setup import DockerState, StubDockerState, add_from_squarespace # this should be called Neo4j State or something
from utils.query import RetreiveRerankQuery

test_squarespace_json_file = "./test/test_squarespace_products.json"

def test_check():
    docker_setup = DockerState()
    assert docker_setup._check()

def test_stubbed_iteration_of_dockerstate():
    docker_setup = StubDockerState()

    for _ in range(0,len(docker_setup.the_states)):
        docker_setup.transition() # will stop at second to last state, success_state

    assert docker_setup.an_error_occurred() == False, "Evidence of success failed to set to True!"
    assert docker_setup.at_success_state() == True, "Iteration did not set success state!"
    assert docker_setup.the_states[docker_setup.at_step] == docker_setup.success_state, "Iteration did not remain at success state!"

    docker_setup.do_action("stop neo4j")
    assert docker_setup.the_states[docker_setup.at_step] == "stop neo4j", "do_action did not advance step!"

def test_docker_neo4j_integration():
    db_filename = './data/artisanal futures database  - Sheet1 - 6-27-2022.csv'
    get_artisans_cypher = "MATCH (n:Artisan) RETURN n"
    docker_setup = DockerState()
    assert docker_setup._start_or_run_neo4j()
    assert docker_setup._upload_data_to_neo4j(db_filename)
    assert 6 == len(docker_setup._check_neo4j_db(what='Artisan'))

    assert len(docker_setup._check_neo4j_db(what='Artisan')) == len(docker_setup._query_database(get_artisans_cypher)), "DB query and check did not return same number of results!"

    assert docker_setup._shutdown_neo4j_db()

def test_ranked_query():
    stub_retriever = lambda: [
        "woman owned, black owned, canvas, transparent plastic, leather, zipper, machine sewing, dye",
        "black owned, food soverignity, community education compost, manure seminar, hands on",
        "woman owned, black owned, human hair, human grown",
        "woman owned, black owned, food soverignity soil, plants, native plants generative, nature",
        "weaver collective, cotton, cloth, dye sewing, dye, weaving",
        "african american civil rights, african culture, african american culture canvas, acrylic paint machine sewing, ink",
        "woman owned, african american owned, cotton, polyester, yarn stitching, air-jet spun, custom design on bulk item cotton, polyester, yarn"
    ] # note t-shirt query at end
    query_against = RetreiveRerankQuery(retriever=stub_retriever)

    query_against.text = "african american owned t-shirt"

    ranking = query_against.method()

    assert ranking.max() == ranking[-1], "t-shirt query did not match t-shirt materials!"


def test_squarespace_upload():
    # requests.get(..., json=true)
    the_json = None
    with open(test_squarespace_json_file) as obj:
        the_json = json.load(obj)
    
    url_getter = lambda x: the_json
    db_writer = lambda x: True

    response = add_from_squarespace(
        url = "https://example.com/?format=json-pretty",
        db_writer=db_writer,
        url_getter=url_getter
    )

    expected_title = "Bone pendants - 45mm - price per pendant"

    assert response is not None, "stubbed fetch, upload failed!"
    assert response['product name'].str.contains(expected_title).any(), f"Expected {expected_title}! Did not find!"

    expected_number_of_rows = 69
    assert expected_number_of_rows == len(response), f"Unexpected size of dataframe, given referenxed fixture {test_squarespace_json_file}"