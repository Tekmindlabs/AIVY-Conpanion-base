import { NextRequest } from "next/server";
import { getServerSession } from "next-auth";
import { authConfig } from "@/lib/auth/config";
import { StreamingTextResponse, LangChainStream } from 'ai';
import { prisma } from "@/lib/prisma";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { createHybridAgent, HybridState } from '@/lib/ai/hybrid-agent';
import { AgentState, ReActStep, EmotionalState } from '@/lib/ai/agents';
import { Message } from '@/types/chat';
import { MemoryService } from '@/lib/memory/memory-service';
import { EmbeddingModel } from '@/lib/knowledge/embeddings';


// Type definitions
interface MemorySearchResponse {
  success: boolean;
  memories: any[];
  error?: string;
}

interface SuccessResponse {
  success: true;
  emotionalState: EmotionalState;
  reactSteps: ReActStep[];
  response: string;
  timestamp: string;
  currentStep: string;
  userId: string;
}

interface ErrorResponse {
  success: false;
  error: string;
  reactSteps: ReActStep[];
  currentStep: string;
  userId: string;
}

type AgentResponse = SuccessResponse | ErrorResponse;

interface ChatMetadata {
  emotionalState: EmotionalState | null;
  reactSteps: Array<{
    thought: string;
    action: string;
    observation: string;
    response?: string;
  }>;
  personalization: {
    learningStyle: string | null;
    difficulty: string | null;
    interests: string[];
  };
  memoryContext?: {
    relevantMemoriesCount: number;
    memoryId: string;
  };
}

// Process steps for better error tracking
const STEPS = {
  INIT: 'Initializing request',
  AUTH: 'Authenticating user',
  PROCESS: 'Processing messages',
  MEMORY_SEARCH: 'Searching memories',
  EMBED: 'Generating embeddings',
  AGENT: 'Processing with hybrid agent',
  RESPONSE: 'Generating response',
  MEMORY_STORE: 'Storing memory',
  STREAM: 'Streaming response'
};

if (!process.env.GOOGLE_AI_API_KEY) {
  throw new Error("GOOGLE_AI_API_KEY is not set");
}

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY);
const memoryService = new MemoryService();
const requestCache = new Map<string, Response>();

export async function POST(req: NextRequest) {
  const runId = crypto.randomUUID();
  let currentStep = STEPS.INIT;
  
  const requestId = req.headers.get('x-request-id') || runId;
  const cachedResponse = requestCache.get(requestId);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    // Authentication
    currentStep = STEPS.AUTH;
    const session = await getServerSession(authConfig);
    if (!session?.user?.id) {
      return new Response(
        JSON.stringify({ error: "Unauthorized" }), 
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Message validation
    const { messages }: { messages: Message[] } = await req.json();
    if (!messages?.length) {
      return new Response(
        JSON.stringify({ error: "Invalid message format - content is required" }), 
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const user = await prisma.user.findUnique({
      where: { id: session.user.id },
      select: {
        id: true,
        learningStyle: true,
        difficultyPreference: true,
        interests: true
      }
    });

    if (!user) {
      return new Response(
        JSON.stringify({ error: "User not found" }), 
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Process messages and search memories
    currentStep = STEPS.PROCESS;
    const processedMessages = messages.map(msg => ({
      ...msg,
      content: msg.content.trim()
    }));

    // After processing messages and getting the last message
const lastMessage = processedMessages[processedMessages.length - 1];
if (!lastMessage?.content) {
  return new Response(
    JSON.stringify({ error: "Invalid last message" }), 
    { status: 400, headers: { 'Content-Type': 'application/json' } }
  );
}

// Search relevant memories
currentStep = STEPS.MEMORY_SEARCH;
const relevantMemories = await memoryService.searchMemories(
  lastMessage.content,
  user.id,
  5
).catch(error => {
  console.warn('Memory search failed:', error);
  return [];
});

// Create memory context string
const memoryContext = relevantMemories
  .map(memory => `Previous interaction: ${memory.content}`)
  .join('\n');

// Generate embeddings
currentStep = STEPS.EMBED;
const embeddingResult = await EmbeddingModel.generateEmbedding(lastMessage.content);
const embedding = Array.from(embeddingResult);
    
    const processedTensors = {
      embedding: embedding,
      input_ids: new Float32Array(embedding.length).fill(0),
      attention_mask: new Float32Array(embedding.length).fill(1),
      token_type_ids: new Float32Array(embedding.length).fill(0)
    };

    // Initialize and process with hybrid agent
    const model = genAI.getGenerativeModel({ model: "gemini-pro" });
    const { stream, handlers } = LangChainStream({
      experimental_streamData: true
    });

    const hybridAgent = createHybridAgent(model, memoryService);
    
    currentStep = STEPS.AGENT;
    const initialState: HybridState = {
      userId: user.id,
      messages: processedMessages,
      currentStep: "initial",
      emotionalState: {
        mood: "neutral",
        confidence: "medium"
      },
      context: {
        role: 'companion',
        analysis: {},
        recommendations: "",
        previousMemories: relevantMemories, // Add memories here
        memoryContext: memoryContext,       // Add memory context
        personalPreferences: {
          interests: user.interests || [],
          communicationStyle: 'default',
          emotionalNeeds: [],
          dailyRoutines: [],
          supportPreferences: []
        },
        relationshipDynamics: {
          trustLevel: 'initial',
          engagementStyle: 'standard',
          connectionStrength: 'new',
          interactionHistory: []
        }
      },
      reactSteps: [],
      processedTensors: {
        embedding: embedding,
        input_ids: new Float32Array(embedding.length).fill(0),
        attention_mask: new Float32Array(embedding.length).fill(1),
        token_type_ids: new Float32Array(embedding.length).fill(0)
      }
    };

    const response = await hybridAgent.process(initialState);
if (!response.success) {
  throw new Error(response.error || "Processing failed");
}

// Store memory
currentStep = STEPS.MEMORY_STORE;
await memoryService.addMemory({
  userId: user.id,
  contentType: 'conversation',
  content: lastMessage.content,
  metadata: {
    messages: processedMessages,
    embedding: embedding,
    emotionalState: response.emotionalState,
    reactStep: response.reactSteps?.[response.reactSteps.length - 1],
    context: initialState.context,
    content_type: 'conversation',
    timestamp: new Date().toISOString()
  }
});

    // Generate personalized response
    currentStep = STEPS.RESPONSE;
    const personalizedResponse = await model.generateContent({
      contents: [{
        role: 'user',
        parts: [{
          text: `
            Context from previous interactions:
            ${memoryContext}
            
            Given this response: "${response.response}"
            Please adapt it for a ${user.learningStyle || 'general'} learner 
            with ${user.difficultyPreference || 'moderate'} difficulty preference.
            Consider their interests: ${user.interests?.join(', ') || 'general topics'}.
            Current emotional state: ${response.emotionalState?.mood}, 
            Confidence: ${response.emotionalState?.confidence}
          `
        }]
      }]
    });

    const finalResponse = personalizedResponse.response.text()
      .replace(/^\d+:/, '')
      .replace(/\\n/g, '\n')
      .trim();

    // Store chat metadata
    const chatMetadata: ChatMetadata = {
      emotionalState: response.emotionalState || null,
      reactSteps: response.reactSteps || [],
      personalization: {
        learningStyle: user.learningStyle || null,
        difficulty: user.difficultyPreference || null,
        interests: user.interests || []
      },
      memoryContext: {
        relevantMemoriesCount: relevantMemories.length,
        memoryId: runId,
        memories: relevantMemories.map(mem => ({
          id: mem.id,
          content: mem.content,
          timestamp: mem.metadata?.timestamp
        }))
      }
    };

    // Store chat in database
    await prisma.chat.create({
      data: {
        userId: user.id,
        message: lastMessage.content,
        response: finalResponse,
        metadata: chatMetadata,
      },
    }).catch((dbError: Error) => {
      console.error("Error saving chat to database:", dbError);
    });

    // Stream response
    currentStep = STEPS.STREAM;
    const messageData: Message = {
      id: runId,
      role: 'assistant',
      content: finalResponse,
      createdAt: new Date()
    };
    
    await handlers.handleLLMNewToken(finalResponse);
    await handlers.handleLLMEnd(messageData, runId);

    const streamResponse = new StreamingTextResponse(stream);
    requestCache.set(requestId, streamResponse.clone());
    return streamResponse;

  } catch (error) {
    console.error(`Failed at step: ${currentStep}`, error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
        details: `Failed during ${currentStep}`,
        stack: error instanceof Error ? error.stack : undefined,
        step: currentStep
      }),
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}