import pandas as pd
import networkx as nx
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def compute_cognitive_load(verified_df):
    """Cognitive load = number of prerequisite ancestors (deterministic)"""
    G = nx.DiGraph()
    prereq_edges = verified_df[verified_df['relation_type'] == 'prerequisite-of']
    for _, row in prereq_edges.iterrows():
        G.add_edge(row['concept_a'], row['concept_b'])

    cognitive_load = {}
    for concept in G.nodes():
        cognitive_load[concept] = len(nx.ancestors(G, concept))

    # Concepts not in the graph get load = 0
    all_concepts = set(verified_df['concept_a'].tolist() +
                       verified_df['concept_b'].tolist())
    for c in all_concepts:
        if c not in cognitive_load:
            cognitive_load[c] = 0

    return cognitive_load

def store_in_neo4j(verified_df, cognitive_load_dict):
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:

        # Clear old data
        session.run("MATCH (n) DETACH DELETE n")
        print("Cleared existing graph.")

        # Get bloom levels per concept
        bloom_levels = {}
        for _, row in verified_df[verified_df['relation_type'] == 'bloom-level'].iterrows():
            bloom_levels[row['concept_b']] = str(row.get('bloom_level', 'understand')).lower()

        # Get all unique concepts
        all_concepts = set(
            verified_df['concept_a'].tolist() +
            verified_df['concept_b'].tolist()
        )

        # Normalize cognitive load to 0-1
        max_load = max(cognitive_load_dict.values()) if cognitive_load_dict else 1

        # Create concept nodes
        for concept in all_concepts:
            load       = cognitive_load_dict.get(concept, 0)
            bloom      = bloom_levels.get(concept, 'understand')
            normalized = round(load / max_load, 3) if max_load > 0 else 0.0

            session.run("""
                MERGE (c:Concept {name: $name})
                SET c.bloom_level            = $bloom,
                    c.cognitive_load         = $load,
                    c.cognitive_load_norm    = $normalized
            """, name=concept, bloom=bloom, load=load, normalized=normalized)

        print(f"Created {len(all_concepts)} concept nodes.")

        # Create edges
        edge_count = 0
        for _, row in verified_df.iterrows():
            rel   = row['relation_type']
            a     = row['concept_a']
            b     = row['concept_b']
            src   = str(row.get('video_id', 'unknown'))
            conf  = str(row.get('confidence', 'medium'))

            if rel == 'prerequisite-of':
                session.run("""
                    MATCH (a:Concept {name:$a}), (b:Concept {name:$b})
                    MERGE (a)-[r:PREREQUISITE_OF]->(b)
                    SET r.weight = 1.0, r.source = $src, r.confidence = $conf
                """, a=a, b=b, src=src, conf=conf)
                edge_count += 1

            elif rel == 'common-misconception-of':
                session.run("""
                    MATCH (a:Concept {name:$a}), (b:Concept {name:$b})
                    MERGE (a)-[r:MISCONCEPTION_OF]->(b)
                    SET r.source = $src
                """, a=a, b=b, src=src)
                edge_count += 1

            elif rel == 'bloom-level':
                bloom = str(row.get('bloom_level', 'understand')).lower()
                session.run("""
                    MATCH (a:Concept {name:$a}), (b:Concept {name:$b})
                    MERGE (a)-[r:BLOOM_RELATION]->(b)
                    SET r.bloom_level = $bloom, r.source = $src
                """, a=a, b=b, bloom=bloom, src=src)
                edge_count += 1

        print(f"Created {edge_count} edges.")

    driver.close()
    print("\n✅ Knowledge graph stored in Neo4j successfully!")

def print_summary(verified_df, cognitive_load_dict):
    print("\n" + "="*50)
    print("COGNITIVE LOAD SUMMARY (deterministic)")
    print("="*50)
    sorted_load = sorted(cognitive_load_dict.items(),
                         key=lambda x: x[1], reverse=True)
    for concept, load in sorted_load:
        bar = "█" * load
        print(f"  {concept:<30} load={load}  {bar}")

if __name__ == "__main__":
    df = pd.read_csv('outputs/relations_verified.csv')
    print(f"Loading {len(df)} verified relations...\n")

    print("Computing cognitive load...")
    cog_load = compute_cognitive_load(df)

    print_summary(df, cog_load)

    print("\nConnecting to Neo4j...")
    store_in_neo4j(df, cog_load)

    print("\n✅ PIPELINE COMPLETE")
    print("Open Neo4j Browser and run:")
    print("  MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100")