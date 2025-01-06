// lib/memory/memory-service.ts
import { getMem0Client } from './mem0-client';
import { getMilvusClient } from '../milvus/client';
import { Driver, driver } from 'neo4j-driver';
import { v4 as uuidv4 } from 'uuid';

export interface MemoryContent {
  userId: string;
  contentType: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface MemoryResult {
  id: string;
  userId: string;
  contentType: string;
  metadata: Record<string, any>;
}

export class MemoryService {
  private memory = getMem0Client();
  private milvus = getMilvusClient();
  private neo4j: Driver;

  // In memory-service.ts constructor
constructor() {
  if (!process.env.NEO4J_URI || !process.env.NEO4J_USERNAME || !process.env.NEO4J_PASSWORD) {
    throw new Error('Neo4j configuration missing');
  }
  
  this.neo4j = Neo4jDriver.driver(
    process.env.NEO4J_URI,
    Neo4jDriver.auth.basic(process.env.NEO4J_USERNAME, process.env.NEO4J_PASSWORD)
  );
}

  async addMemory({
    userId,
    contentType,
    content,
    metadata = {}
  }: MemoryContent): Promise<MemoryResult> {
    const session = this.neo4j.session();
    try {
      const enrichedMetadata = {
        ...metadata,
        content_type: contentType,
        content_id: uuidv4(),
        timestamp: new Date().toISOString()
      };

      // Store in Mem0/Milvus
      const result = await this.memory.add(
        content,
        userId,
        enrichedMetadata
      );

      if (!result.success) {
        throw new Error(result.error || 'Failed to add memory');
      }

      // Store in Neo4j with relationships
      await session.run(
        `
        CREATE (m:Memory {
          userId: $userId,
          contentId: $contentId,
          content: $content,
          contentType: $contentType,
          timestamp: datetime()
        })
        WITH m
        MATCH (u:User {id: $userId})
        CREATE (u)-[:CREATED]->(m)
        `,
        {
          userId,
          contentId: enrichedMetadata.content_id,
          content,
          contentType,
          metadata: JSON.stringify(enrichedMetadata)
        }
      );

      // Create relationships if specified in metadata
      if (metadata.relationships) {
        for (const relationship of metadata.relationships) {
          await session.run(
            `
            MATCH (m1:Memory {contentId: $sourceId})
            MATCH (m2:Memory {contentId: $targetId})
            CREATE (m1)-[:${relationship.type} {metadata: $metadata}]->(m2)
            `,
            {
              sourceId: enrichedMetadata.content_id,
              targetId: relationship.targetId,
              metadata: JSON.stringify(relationship.metadata || {})
            }
          );
        }
      }

      return {
        id: enrichedMetadata.content_id,
        userId,
        contentType,
        metadata: enrichedMetadata
      };
    } catch (error) {
      console.error('Error adding memory:', error);
      throw new Error('Failed to add memory');
    } finally {
      await session.close();
    }
  }

  async searchMemories(query: string, userId: string, limit: number = 5): Promise<any[]> {
    if (!query || !userId) {
      throw new Error('Query and userId are required for searching memories');
    }

    const session = this.neo4j.session();
    try {
      // Search in Mem0/Milvus
      const vectorResult = await this.memory.search(query, userId, limit);
      
      // Enhanced Neo4j search with relationship context
      const graphResult = await session.run(
        `
        MATCH (m:Memory {userId: $userId})
        WITH m
        OPTIONAL MATCH (m)-[r]-(related)
        WITH m, collect(related) as relatedNodes
        RETURN m, relatedNodes
        ORDER BY m.timestamp DESC
        LIMIT $limit
        `,
        { userId, limit }
      );

      const memories = vectorResult?.results?.results || [];
      const graphMemories = graphResult.records.map(record => ({
        ...record.get('m').properties,
        relationships: record.get('relatedNodes').map((node: any) => node.properties)
      }));

      // Combine and deduplicate results with relationship context
      const combinedResults = [...memories, ...graphMemories];
      const uniqueResults = Array.from(new Set(combinedResults.map(m => m.contentId)))
        .map(id => {
          const memory = combinedResults.find(m => m.contentId === id);
          return {
            id: memory.contentId || memory.id,
            userId: memory.userId,
            content: memory.content,
            messages: memory.metadata?.messages || [],
            timestamp: memory.metadata?.timestamp || memory.timestamp,
            metadata: memory.metadata || {},
            relationships: memory.relationships || []
          };
        });

      return uniqueResults;

    } catch (error) {
      console.error('Error searching memories:', error);
      throw new Error('Failed to search memories');
    } finally {
      await session.close();
    }
  }

  async deleteMemory(userId: string, memoryId: string): Promise<boolean> {
    const session = this.neo4j.session();
    try {
      // Delete from Mem0/Milvus
      const result = await this.memory.delete(userId, memoryId);

      // Delete from Neo4j with relationship cleanup
      await session.run(
        `
        MATCH (m:Memory {userId: $userId, contentId: $memoryId})
        OPTIONAL MATCH (m)-[r]-()
        DELETE r, m
        `,
        { userId, memoryId }
      );

      return result.success;
    } catch (error) {
      console.error('Error deleting memory:', error);
      throw new Error('Failed to delete memory');
    } finally {
      await session.close();
    }
  }

  async close() {
    try {
      await this.neo4j.close();
    } catch (error) {
      console.error('Error closing Neo4j connection:', error);
    }
  }
}