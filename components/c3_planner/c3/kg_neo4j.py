"""L0: load C1's knowledge graph straight from Neo4j.

Reads all four C1 edge types and turns them into C3's KnowledgeGraph:
  PREREQUISITE_OF (weight)  -> strong ones (>= 0.7) become hard prerequisites (rule R1),
                               weak ones are kept as "weak_prerequisites" (hints only)
  HAS_COGNITIVE_LOAD        -> "difficulty" used by the ZPD rule (R2)
  HAS_BLOOM_LEVEL           -> "bloom" / "bloom_rank" (passed on, used later for BloomJump)
  COMMON_MISCONCEPTION_OF   -> misconceptions (rule R5)

Connection details come from the .env file (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD).
"""
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from .kg import KnowledgeGraph

STRONG_THRESHOLD = 0.7

CONCEPTS_QUERY = """
MATCH (c:Concept)
OPTIONAL MATCH (c)-[:HAS_COGNITIVE_LOAD]->(l:LoadLevel)
OPTIONAL MATCH (c)-[:HAS_BLOOM_LEVEL]->(b:BloomLevel)
OPTIONAL MATCH (p:Concept)-[r:PREREQUISITE_OF]->(c)
RETURN c.id AS id, c.name AS name, l.level AS load,
       b.name AS bloom, b.rank AS bloom_rank,
       collect(CASE WHEN p IS NULL THEN null ELSE {pre: p.id, w: r.weight} END) AS pres
"""

MISCONCEPTIONS_QUERY = """
MATCH (m:Misconception)-[:COMMON_MISCONCEPTION_OF]->(c:Concept)
RETURN m.id AS id, c.id AS affects, m.description AS description
"""


def load_kg_from_neo4j(strong_threshold: float = STRONG_THRESHOLD) -> KnowledgeGraph:
    load_dotenv()
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
    )
    concepts, misconceptions = {}, {}
    try:
        with driver.session() as s:
            for r in s.run(CONCEPTS_QUERY):
                pres = [x for x in r["pres"] if x]
                concepts[r["id"]] = {
                    "name": r["name"] or r["id"],
                    "difficulty": int(r["load"] or 1),
                    "bloom": r["bloom"],
                    "bloom_rank": r["bloom_rank"],
                    "prerequisites": sorted(x["pre"] for x in pres
                                            if (x["w"] or 0) >= strong_threshold),
                    "weak_prerequisites": sorted(x["pre"] for x in pres
                                                 if (x["w"] or 0) < strong_threshold),
                }
            for r in s.run(MISCONCEPTIONS_QUERY):
                misconceptions[r["id"]] = {"affects": r["affects"],
                                           "description": r["description"] or ""}
    finally:
        driver.close()

    if not concepts:
        raise RuntimeError("No Concept nodes found in Neo4j. Is the right database running?")
    kg = KnowledgeGraph(concepts, misconceptions)
    kg.validate()
    return kg
