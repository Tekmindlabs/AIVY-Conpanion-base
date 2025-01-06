// /lib/neo4j/client.ts
import { Neo4jDriver, driver } from 'neo4j-driver';

class Neo4jConnection {
  private static instance: Neo4jDriver;

  private constructor() {}

  public static getInstance(): Neo4jDriver {
    if (!Neo4jConnection.instance) {
      if (!process.env.NEO4J_URL || !process.env.NEO4J_USER || !process.env.NEO4J_PASSWORD) {
        throw new Error('Neo4j configuration missing: NEO4J_URL, NEO4J_USER, and NEO4J_PASSWORD are required');
      }

      Neo4jConnection.instance = driver(
        process.env.NEO4J_URL,
        driver.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASSWORD)
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