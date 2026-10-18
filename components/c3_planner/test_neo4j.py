import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

query = """
MATCH (p:Concept)-[:PREREQUISITE_OF*]->(:Concept {id:$target})
RETURN DISTINCT p.id AS id ORDER BY id
"""

with driver.session() as session:
    result = session.run(query, target="heap")
    print("Heap needs:", [row["id"] for row in result])

driver.close()