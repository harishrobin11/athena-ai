import os
from neo4j import GraphDatabase, AsyncGraphDatabase
from app.core.logger import logger

class Neo4jManager:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "athena_password")
        self.driver = None
        self.async_driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.async_driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Connected to Neo4j Knowledge Graph successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")

    def close(self):
        if self.driver:
            self.driver.close()
        if self.async_driver:
            import asyncio
            asyncio.create_task(self.async_driver.close())

neo4j_manager = Neo4jManager()
