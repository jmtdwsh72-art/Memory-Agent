#!/usr/bin/env python3
"""
Interactive REPL agent using zep-cloud for memory management.
Demonstrates memory recall and storage with optional Anthropic integration.
"""
import os
from dotenv import load_dotenv
from zep_cloud import Zep
from zep_cloud.types import Message
import uuid

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class MemoryAgent:
    def __init__(self):
        load_dotenv()
        
        # Initialize Zep client
        zep_api_key = os.getenv("ZEP_API_KEY")
        if not zep_api_key or zep_api_key == "your_zep_key_here":
            raise ValueError("Please set ZEP_API_KEY in your .env file")
        
        zep_api_url = os.getenv("ZEP_API_URL")
        if zep_api_url:
            self.zep = Zep(api_key=zep_api_key, api_url=zep_api_url)
        else:
            self.zep = Zep(api_key=zep_api_key)
        
        # Initialize Anthropic client (optional)
        self.anthropic_client = None
        if ANTHROPIC_AVAILABLE:
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_api_key and anthropic_api_key != "your_anthropic_key_here":
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Generate a unique session ID for this conversation
        self.session_id = str(uuid.uuid4())
        print(f"Session ID: {self.session_id}")
        print("Memory Agent initialized. Type 'quit' to exit.\n")
    
    def get_memory_context(self):
        """Retrieve memory context from Zep for the current session."""
        try:
            memory = self.zep.memory.get(session_id=self.session_id)
            if hasattr(memory, 'context') and memory.context:
                return memory.context
            else:
                return "No previous context found."
        except Exception as e:
            print(f"Warning: Could not retrieve memory context: {e}")
            return "Memory retrieval failed."
    
    def add_to_memory(self, user_message: str, assistant_message: str):
        """Add both user and assistant messages to Zep memory."""
        try:
            messages = [
                Message(role_type="user", content=user_message),
                Message(role_type="assistant", content=assistant_message)
            ]
            self.zep.memory.add(session_id=self.session_id, messages=messages)
        except Exception as e:
            print(f"Warning: Could not add to memory: {e}")
    
    def get_llm_response(self, user_message: str, memory_context: str) -> str:
        """Get response from Anthropic LLM if available, otherwise return a simple echo."""
        if self.anthropic_client:
            try:
                system_prompt = f"""You are a helpful assistant with access to previous conversation context.

MEMORY_CONTEXT:
{memory_context}

Use this context to provide relevant, personalized responses. Reference previous information when appropriate."""
                
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}]
                )
                return response.content[0].text
            except Exception as e:
                return f"LLM Error: {e}. Echoing your message: {user_message}"
        else:
            return f"[No LLM configured] Echo: {user_message}"
    
    def run(self):
        """Main REPL loop."""
        while True:
            try:
                # Get user input
                user_input = input("\n🤖 You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Step 2: Retrieve memory context
                print("\n📝 Retrieving memory context...")
                memory_context = self.get_memory_context()
                print(f"Memory Context: {memory_context}")
                
                # Step 3: Get LLM response
                print("\n🧠 Generating response...")
                assistant_response = self.get_llm_response(user_input, memory_context)
                print(f"\n🤖 Assistant: {assistant_response}")
                
                # Step 4: Add both messages to memory
                print("\n💾 Storing in memory...")
                self.add_to_memory(user_input, assistant_response)
                print("Stored successfully!")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    try:
        agent = MemoryAgent()
        agent.run()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        print("Make sure you have set ZEP_API_KEY in your .env file")


if __name__ == "__main__":
    main()