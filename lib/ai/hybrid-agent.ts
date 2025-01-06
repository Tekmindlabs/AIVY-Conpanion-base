import { v4 as uuidv4 } from 'uuid';
import { GoogleGenerativeAI } from "@google/generative-ai";
import { createEmotionalAgent } from "./emotional-agent";
import { MemoryService } from "../memory/memory-service";
import { Message } from "@/types/chat";
import { AgentState, EmotionalState, AgentRole } from "./agents";
import { MemoryTools } from "../memory/memory-tools";

// Define base interfaces
interface ReActStep {
  thought: string;
  action: string;
  observation: string;
  response?: string;
}

interface Memory {
  id: string;
  content: string;
  emotionalState: EmotionalState;
  timestamp: string;
  userId: string;
  metadata?: {
    learningStyle?: string;
    difficulty?: string;
    interests?: string[];
    contentType?: string;
    context?: any;
    messages?: Message[];
  };
}

interface SearchResult {
  id: string;
  content: string;
  userId: string;
  metadata?: any;
}

export interface HybridState extends AgentState {
  reactSteps: ReActStep[];
  currentStep: string;
  userId: string;
  messages: Message[];
  context: {
    role: AgentRole;
    analysis: {
      emotional?: any;
      research?: any;
      validation?: any;
    };
    recommendations: string;
    previousMemories?: Memory[];
    personalPreferences: {
      interests?: string[];
      communicationStyle?: string;
      emotionalNeeds?: string[];
      dailyRoutines?: string[];
      supportPreferences?: string[];
    };
    relationshipDynamics: {
      trustLevel?: string;
      engagementStyle?: string;
      connectionStrength?: string;
      interactionHistory?: string[];
    };
  };
  processedTensors?: {
    embedding: number[];
    input_ids: Float32Array;
    attention_mask: Float32Array;
    token_type_ids: Float32Array;
  };
}

interface HybridResponse {
  success: boolean;
  emotionalState?: EmotionalState;
  reactSteps?: ReActStep[];
  response?: string;
  error?: string;
  timestamp: string;
  currentStep: string;
  userId: string;
}

const createMessage = (content: string, role: 'user' | 'assistant'): Message => ({
  id: uuidv4(),
  content,
  role,
  createdAt: new Date()
});

export const createHybridAgent = (model: any, memoryService: MemoryService) => {
  const emotionalAgent = createEmotionalAgent(model);
  const memoryTools = new MemoryTools(memoryService);

  const calculateConnectionStrength = (dynamics: any): string => {
    const interactionCount = dynamics.interactionHistory?.length || 0;
    const trustLevel = dynamics.trustLevel || 'building';
    
    if (interactionCount > 20 && trustLevel === 'high') return 'strong';
    if (interactionCount > 10) return 'moderate';
    return 'building';
  };

  const executeReActStep = async (
    step: string, 
    state: HybridState,
    emotionalState: EmotionalState,
    memories: Memory[]
  ): Promise<ReActStep> => {
    const memoryContext = memories
      .map((memory: Memory) => 
        `Memory: ${memory.content} (Emotional: ${memory.emotionalState?.mood || 'Unknown'})`
      )
      .join('\n');

    const prompt = `
      As an empathetic AI companion with memory context:
      
      Memory Context:
      ${memoryContext}
      
      Current Emotional State: ${emotionalState.mood} (Confidence: ${emotionalState.confidence})
      Current User Context:
      - Trust Level: ${state.context.relationshipDynamics.trustLevel}
      - Connection Strength: ${state.context.relationshipDynamics.connectionStrength}
      - Previous Interactions: ${state.context.relationshipDynamics.interactionHistory?.join(', ')}
      
      User Preferences:
      - Communication Style: ${state.context.personalPreferences.communicationStyle}
      - Interests: ${state.context.personalPreferences.interests?.join(', ')}
      
      Current Situation: ${step}
    `;

    const result = await model.generateContent({
      contents: [{
        role: "user",
        parts: [{ text: prompt }]
      }]
    });
    
    const response = result.response.text();
    const [thought, action, observation] = response.split('\n');
    
    return {
      thought: thought || 'Processing input',
      action: action || 'Generating response',
      observation: observation || 'Analyzing interaction'
    };
  };

  return {
    process: async (state: HybridState): Promise<HybridResponse> => {
      try {
        const lastMessage = state.messages[state.messages.length - 1];
        if (!lastMessage?.content) {
          throw new Error("Invalid message format - content is required");
        }

        // Transform search results into Memory objects
        const searchResults = await memoryService.searchMemories(
          lastMessage.content,
          state.userId,
          5
        ) as SearchResult[];

        const relevantMemories: Memory[] = searchResults.map((result: SearchResult): Memory => ({
          id: result.id,
          content: result.content,
          emotionalState: result.metadata?.emotionalState || { 
            mood: 'neutral', 
            confidence: 'medium' 
          },
          timestamp: result.metadata?.timestamp || new Date().toISOString(),
          userId: result.userId,
          metadata: result.metadata
        }));

        const emotionalAnalysis = await emotionalAgent({
          ...state,
          context: {
            ...state.context,
            previousMemories: relevantMemories
          }
        });

        const reactStep = await executeReActStep(
          state.currentStep,
          state,
          emotionalAnalysis.emotionalState,
          relevantMemories
        );

        const response = await model.generateContent({
          contents: [{ 
            role: "user", 
            parts: [{ text: lastMessage.content }]
          }]
        });

        const newMemory = {
          userId: state.userId,
          content: lastMessage.content,
          metadata: {
            messages: [createMessage(lastMessage.content, 'user')],
            emotionalState: emotionalAnalysis.emotionalState,
            reactStep,
            context: state.context,
            timestamp: new Date().toISOString()
          }
        };

        await memoryService.addMemory(newMemory);

        if (state.context.relationshipDynamics.interactionHistory) {
          state.context.relationshipDynamics.interactionHistory.push(lastMessage.content);
        }
        
        state.context.relationshipDynamics.connectionStrength = 
          calculateConnectionStrength(state.context.relationshipDynamics);

        const responseText = response.response.text();

        return {
          success: true,
          emotionalState: emotionalAnalysis.emotionalState,
          reactSteps: [...(state.reactSteps || []), reactStep],
          response: responseText,
          timestamp: new Date().toISOString(),
          currentStep: state.currentStep,
          userId: state.userId
        };

      } catch (error) {
        console.error("Hybrid agent error:", error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
          reactSteps: state.reactSteps || [],
          timestamp: new Date().toISOString(),
          currentStep: state.currentStep,
          userId: state.userId
        };
      }
    }
  };
};