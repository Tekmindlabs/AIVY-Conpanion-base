import React, { useState } from 'react';
import { useChat } from 'ai/react';
import { ChatMessage } from './chat-message';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Send } from 'lucide-react';
import { Card } from '../ui/card';
import { toast } from '../ui/use-toast';
import { Message } from 'ai';

// Add type guard for message roles
function isValidMessageRole(role: string): role is 'system' | 'user' | 'assistant' {
  return ['system', 'user', 'assistant'].includes(role);
}

// Add interface for enhanced message
interface EnhancedMessage extends Omit<Message, 'role'> {
  role: 'system' | 'user' | 'assistant';
  reactSteps?: {
    thought: string;
    action: string;
    observation: string;
  }[];
}

export function ChatContainer() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    onError: (error) => {
      setIsSubmitting(false);
      toast({
        title: "Error",
        description: error.message || "Failed to send message. Please try again.",
        variant: "destructive"
      });
    }
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting || !input.trim()) return;

    try {
      setIsSubmitting(true);
      await handleSubmit(e);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto p-4">
      <Card className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => {
            // Filter out messages with unsupported roles
            if (!isValidMessageRole(message.role)) {
              return null;
            }

            // Convert Message to EnhancedMessage
            const enhancedMessage: EnhancedMessage = {
              ...message,
              role: message.role,
              // Add any additional properties needed by ChatMessage
              reactSteps: []  // Add empty reactSteps array or actual steps if available
            };

            return (
              <ChatMessage 
                key={message.id} 
                message={enhancedMessage}
                isLoading={isLoading && message.role === 'assistant'}
              />
            );
          })}
        </div>
        
        <form
          onSubmit={onSubmit}
          className="border-t p-4 flex gap-2 items-center"
        >
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder="Type your message..."
            className="flex-1"
            disabled={isSubmitting || isLoading}
          />
          <Button 
            type="submit" 
            size="icon"
            disabled={isSubmitting || isLoading || !input.trim()}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}