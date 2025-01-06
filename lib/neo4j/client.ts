// /lib/neo4j/client.ts
import neo4j, { Driver } from 'neo4j-driver';
import 'dotenv/config';
class Neo4jConnection {
  private static instance: Driver;

  private constructor() {}

  public static getInstance(): Driver {
    if (!Neo4jConnection.instance) {
      if (!process.env.NEO4J_URL || !process.env.NEO4J_USER || !process.env.NEO4J_PASSWORD) {
        throw new Error('Neo4j configuration missing: NEO4J_URL, NEO4J_USER, and NEO4J_PASSWORD are required');
      }

      Neo4jConnection.instance = neo4j.driver(
        process.env.NEO4J_URL,
        neo4j.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
      );
    }
    return Neo4jConnection.instance;
  }

  public static async close() {
    if (Neo4jConnection.instance) {
      await Neo4jConnection.instance.close();
    }
  }
}

export const getNeo4jClient = () => Neo4jConnection.getInstance();