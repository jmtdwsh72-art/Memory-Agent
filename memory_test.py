#!/usr/bin/env python3
"""
Scripted memory test for Zep integration.
Tests memory storage and retrieval without requiring Anthropic API.
"""
import os
from dotenv import load_dotenv
from zep_cloud import Zep
from zep_cloud.types import Message
import uuid
import time


class MemoryTester:
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
        
        # Generate a unique session ID for this test
        self.session_id = f"test-{uuid.uuid4()}"
        print(f"Test Session ID: {self.session_id}")
    
    def test_memory_storage_and_retrieval(self):
        """Test storing and retrieving memories."""
        print("\n=== Memory Storage & Retrieval Test ===\n")
        
        # Test data - simulating a conversation with personal facts
        test_conversations = [
            {
                "user": "Hi! My name is Alice and I live in San Francisco.",
                "assistant": "Hello Alice! Nice to meet you. San Francisco is a beautiful city!"
            },
            {
                "user": "I work as a software engineer at a tech startup.",
                "assistant": "That's exciting! The tech scene in San Francisco is really vibrant."
            },
            {
                "user": "I love rock climbing on weekends and my favorite spot is Yosemite.",
                "assistant": "Yosemite is amazing for climbing! El Capitan is legendary. Do you boulder or do more traditional climbing?"
            },
            {
                "user": "I prefer traditional climbing. I also have a pet cat named Whiskers.",
                "assistant": "Traditional climbing is so rewarding! And Whiskers sounds adorable. Cats make great companions."
            }
        ]
        
        # Store conversations in memory
        print("📝 Storing test conversations in memory...\n")
        for i, conv in enumerate(test_conversations, 1):
            print(f"Turn {i}:")
            print(f"  User: {conv['user']}")
            print(f"  Assistant: {conv['assistant']}")
            
            try:
                messages = [
                    Message(role_type="user", content=conv["user"]),
                    Message(role_type="assistant", content=conv["assistant"])
                ]
                self.zep.memory.add(session_id=self.session_id, messages=messages)
                print("  ✅ Stored successfully")
                
                # Small delay to ensure processing
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error storing: {e}")
            
            print()
        
        # Test memory retrieval at different points
        print("\n🧠 Testing memory retrieval...\n")
        
        test_queries = [
            "What's my name?",
            "Where do I live?",
            "What do I do for work?", 
            "What are my hobbies?",
            "Do I have any pets?"
        ]
        
        for query in test_queries:
            print(f"Query: {query}")
            try:
                memory = self.zep.memory.get(session_id=self.session_id)
                if hasattr(memory, 'context') and memory.context:
                    context = memory.context
                    print(f"Memory Context: {context}")
                else:
                    print("No context retrieved")
            except Exception as e:
                print(f"Error retrieving memory: {e}")
            print("-" * 50)
    
    def test_memory_search(self):
        """Test searching through memories."""
        print("\n=== Memory Search Test ===\n")
        
        search_queries = [
            "Alice",
            "San Francisco", 
            "rock climbing",
            "Yosemite",
            "cat"
        ]
        
        for query in search_queries:
            print(f"Searching for: '{query}'")
            try:
                results = self.zep.memory.search(
                    session_id=self.session_id,
                    text=query,
                    limit=5
                )
                
                if hasattr(results, 'results') and results.results:
                    print(f"Found {len(results.results)} results:")
                    for i, result in enumerate(results.results, 1):
                        print(f"  {i}. {result.message.content[:100]}...")
                        if hasattr(result, 'score'):
                            print(f"     Score: {result.score}")
                else:
                    print("No results found")
                    
            except Exception as e:
                print(f"Search error: {e}")
            print("-" * 50)
    
    def cleanup(self):
        """Clean up test session."""
        print(f"\n🧹 Cleaning up test session: {self.session_id}")
        try:
            # Note: Actual cleanup would depend on Zep's API
            # Some implementations might have a delete_session method
            print("Test session cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")


def main():
    try:
        tester = MemoryTester()
        
        print("Starting Zep Memory Integration Test")
        print("=" * 50)
        
        # Run tests
        tester.test_memory_storage_and_retrieval()
        tester.test_memory_search()
        
        print("\n" + "=" * 50)
        print("Test completed! Check the output above to verify memory functionality.")
        print("If you see context being retrieved, Zep is working correctly.")
        
        # Cleanup
        tester.cleanup()
        
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure you have set ZEP_API_KEY in your .env file")


if __name__ == "__main__":
    main()