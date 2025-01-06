// lib/memory/memory-service.ts
import { getMem0Client } from './mem0-client';
import { getMilvusClient } from '../milvus/client';
import { Neo4jDriver } from 'neo4j-driver';
import { v4 as uuidv4 } from 'uuid';

export interface MemoryContent {
  userId: string;
  contentType: string;
  content: string;
  metadata?: Record<string, any>;
}

export class MemoryService {
  private memory = getMem0Client();
  private milvus = getMilvusClient();
  private neo4j: Neo4jDriver;

  constructor() {
    this.neo4j = Neo4jDriver.driver(
      process.env.NEO4J_URL!,
      Neo4jDriver.auth.basic(process.env.NEO4J_USER!, process.env.NEO4J_PASSWORD!)
    );
  }

  async addMemory({
    userId,
    contentType,
    content,
    metadata = {}
  }: MemoryContent): Promise<MemoryResult> {
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

      // Store in Neo4j for relationship tracking
      const session = this.neo4j.session();
      await session.run(
        `CREATE (m:Memory {
          userId: $userId,
          contentId: $contentId,
          content: $content,
          contentType: $contentType,
          timestamp: datetime()
        })`,
        {
          userId,
          contentId: enrichedMetadata.content_id,
          content,
          contentType
        }
      );

      if (!result.success) {
        throw new Error(result.error || 'Failed to add memory');
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
    }
  }

  async searchMemories(query: string, userId: string, limit: number = 5): Promise<any[]> {
    if (!query || !userId) {
      throw new Error('Query and userId are required for searching memories');
    }

    try {
      // Search in Mem0/Milvus
      const vectorResult = await this.memory.search(query, userId, limit);
      
      // Search in Neo4j
      const session = this.neo4j.session();
      const graphResult = await session.run(
        `MATCH (m:Memory)
         WHERE m.userId = $userId
         WITH m
         ORDER BY m.timestamp DESC
         LIMIT $limit
         RETURN m`,
        { userId, limit }
      );

      const memories = vectorResult?.results?.results || [];
      const graphMemories = graphResult.records.map(record => record.get('m').properties);

      // Combine and deduplicate results
      const combinedResults = [...memories, ...graphMemories];
      const uniqueResults = Array.from(new Set(combinedResults.map(m => m.contentId)))
        .map(id => combinedResults.find(m => m.contentId === id));

      return uniqueResults.map(entry => ({
        id: entry.contentId || entry.id,
        userId: entry.userId,
        messages: entry.metadata?.messages || [],
        timestamp: entry.metadata?.timestamp || entry.timestamp,
        metadata: entry.metadata || {}
      }));

    } catch (error) {
      console.error('Error searching memories:', error);
      throw new Error('Failed to search memories');
    }
  }

  async deleteMemory(userId: string, memoryId: string): Promise<boolean> {
    try {
      // Delete from Mem0/Milvus
      const result = await this.memory.delete(userId, memoryId);

      // Delete from Neo4j
      const session = this.neo4j.session();
      await session.run(
        `MATCH (m:Memory {userId: $userId, contentId: $memoryId})
         DELETE m`,
        { userId, memoryId }
      );

      return result.success;
    } catch (error) {
      console.error('Error deleting memory:', error);
      throw new Error('Failed to delete memory');
    }
  }

  async close() {
    await this.neo4j.close();
  }
}