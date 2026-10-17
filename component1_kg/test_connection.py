import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load secrets from .env
load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

try:
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j successfully!")
except Exception as e:
    print("Connection failed:", e)