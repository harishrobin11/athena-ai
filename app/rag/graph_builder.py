import json
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.agent_framework.supervisor import azure_llm
from app.db.neo4j import neo4j_manager
from app.core.logger import logger

GRAPH_EXTRACTION_PROMPT = """
You are an expert Knowledge Graph architect. 
Extract entities and relationships from the following text chunk.

Rules:
1. Extract nodes (entities) and edges (relationships).
2. Nodes must have an 'id' (normalized name), 'label' (e.g., Person, Organization, Location, Technology, Concept).
3. Edges must have a 'source' (node id), 'target' (node id), and 'type' (e.g., FOUNDED, ACQUIRED, WORKS_AT, RELATES_TO).
4. Output strictly as JSON in the following format:
{
  "nodes": [{"id": "Microsoft", "label": "Organization"}],
  "edges": [{"source": "Microsoft", "target": "GitHub", "type": "ACQUIRED", "properties": {"year": 2018}}]
}
Do not include markdown backticks. Just the raw JSON.
"""

async def extract_and_store_graph(text: str, document_id: int):
    """
    Extracts entities and relationships using Azure OpenAI and stores them in Neo4j.
    """
    if not neo4j_manager.async_driver:
        logger.warning("Neo4j driver not initialized. Skipping graph extraction.")
        return

    sys_prompt = SystemMessage(content=GRAPH_EXTRACTION_PROMPT)
    user_prompt = HumanMessage(content=f"Extract graph from this text:\n\n{text}")

    try:
        logger.info("Extracting knowledge graph entities...")
        response = await azure_llm.ainvoke([sys_prompt, user_prompt])
        content = response.content.strip().replace("```json", "").replace("```", "")
        graph_data = json.loads(content)

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Execute Cypher queries
        async with neo4j_manager.async_driver.session() as session:
            # 1. Merge Nodes
            for node in nodes:
                node_id = str(node.get("id", "")).strip().replace("'", "").replace('"', "")
                label = str(node.get("label", "Entity")).strip().replace(" ", "")
                if not node_id:
                    continue
                # Simple Cypher merge
                query = f"MERGE (n:`{label}` {{id: $id, document_id: $doc_id}})"
                await session.run(query, id=node_id, doc_id=document_id)

            # 2. Merge Edges
            for edge in edges:
                source = str(edge.get("source", "")).strip().replace("'", "").replace('"', "")
                target = str(edge.get("target", "")).strip().replace("'", "").replace('"', "")
                rel_type = str(edge.get("type", "RELATES_TO")).strip().replace(" ", "_").upper()
                
                if not source or not target:
                    continue
                    
                query = f"""
                MATCH (a {{id: $source}})
                MATCH (b {{id: $target}})
                MERGE (a)-[r:`{rel_type}`]->(b)
                """
                await session.run(query, source=source, target=target)

        logger.info(f"Successfully committed {len(nodes)} nodes and {len(edges)} edges to Neo4j.")
    
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from LLM graph extraction.")
    except Exception as e:
        logger.error(f"Graph extraction failed: {e}")
