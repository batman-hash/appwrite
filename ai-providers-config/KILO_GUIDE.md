"""
Kilo Code - Quick Usage Guide
"""

# ============================================================================
# 1. BASIC SETUP
# ============================================================================

"""
Step 1: Get your Kilo API key
  1. Go to https://kilo.ai/dashboard
  2. Navigate to Settings → API Keys
  3. Create new API key
  4. Copy to .env as KILO_API_KEY

Step 2: Install dependencies
  pip install requests python-dotenv

Step 3: Create .env file
  KILO_API_KEY=your_key_here
"""

# ============================================================================
# 2. SIMPLE USAGE
# ============================================================================

from kilo_advanced import KiloAdvancedClient

# Initialize client
client = KiloAdvancedClient()

# Simple chat
response = client.chat("What is machine learning?")
print(response["content"])

# ============================================================================
# 3. SELECT DIFFERENT MODELS
# ============================================================================

# Fast model
response = client.chat(
    "Who won the 2023 World Cup?",
    model="kilo-fast"
)
print(response)

# Quality model (slower but better)
response = client.chat(
    "Explain quantum computing",
    model="kilo-quality"
)
print(response)

# Code specialist
response = client.chat(
    "Write Python to fetch API data",
    model="kilo-code"
)
print(response)

# ============================================================================
# 4. STREAMING RESPONSES
# ============================================================================

print("Streaming response:")
client.stream_chat("Tell me a story about robots")

# ============================================================================
# 5. CUSTOM PARAMETERS
# ============================================================================

response = client.chat(
    "Write a creative poem",
    model="kilo-auto/free",
    temperature=0.9,  # More creative
    max_tokens=500,   # Longer response
    top_p=0.95        # More varied
)
print(response["content"])

# ============================================================================
# 6. SYSTEM PROMPTS
# ============================================================================

response = client.chat(
    "What is 2 + 2?",
    system_prompt="You are a math tutor. Explain always.",
    model="kilo-auto/free"
)
print(response["content"])

# ============================================================================
# 7. TRACK USAGE
# ============================================================================

# Make multiple requests
for i in range(3):
    client.chat(f"Question {i}: Tell me about topic {i}")

# Get stats
stats = client.get_request_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Success rate: {stats['success_rate']}")

# ============================================================================
# 8. ERROR HANDLING
# ============================================================================

response = client.chat("Test message")

if "error" in response:
    print(f"Error: {response['error']}")
else:
    print(f"Success: {response['content']}")

# ============================================================================
# 9. WITH LANGCHAIN
# ============================================================================

"""
from langchain_openai import ChatOpenAI

kilo = ChatOpenAI(
    api_key="your_kilo_api_key",
    base_url="https://api.kilo.ai/v1",
    model="kilo-auto/free"
)

# Use like any LangChain LLM
response = kilo.invoke("What is AI?")
print(response.content)
"""

# ============================================================================
# 10. BEST PRACTICES
# ============================================================================

"""
1. Use kilo-auto/free for general tasks (free tier)
2. Use kilo-fast for quick responses
3. Use kilo-code for programming help
4. Use kilo-reasoning for complex problems
5. Set temperature lower (0.3-0.5) for accuracy
6. Set temperature higher (0.7-0.9) for creativity
7. Monitor usage with get_request_stats()
8. Always handle errors in production
9. Use system_prompt for consistent behavior
10. Stream for better UX on long responses
"""

# ============================================================================
# 11. COST ESTIMATION
# ============================================================================

"""
Kilo Pricing (approximate):

Free Tier:
  - kilo-auto/free: Limited requests/day
  - Perfect for testing and prototyping
  
Premium:
  - Pay-per-token model
  - 1000 tokens ≈ $0.001-0.01
  - Varies by model
  
Cost Tips:
  - Use free tier first
  - Set reasonable max_tokens
  - Cache similar requests if possible
  - Use faster models for simple tasks
"""

# ============================================================================
# 12. MODELS AVAILABLE
# ============================================================================

"""
kilo-auto/free
  → Auto-selects best free model
  → Best for prototyping
  → Requests/day: Limited
  → Speed: Good
  
kilo-fast
  → Ultra-fast responses
  → Best for: Real-time apps, chat
  → Latency: <500ms
  
kilo-balanced
  → Balance of speed and quality
  → Best for: General purpose
  
kilo-quality
  → Best quality responses
  → Best for: Complex tasks
  → Latency: 2-5s
  
kilo-code
  → Specialized for code
  → Best for: Programming tasks
  
kilo-reasoning
  → Enhanced reasoning
  → Best for: Logic puzzles, analysis
"""

# ============================================================================
# 13. RATE LIMITS (Free Tier)
# ============================================================================

"""
Requests per minute: 100
Requests per hour: 10,000
Tokens per minute: 90,000

If you hit limits:
  - Wait a minute
  - Upgrade to premium
  - Use batch processing
"""

# ============================================================================
# 14. TROUBLESHOOTING
# ============================================================================

"""
Problem: "KILO_API_KEY not set"
Solution: 
  export KILO_API_KEY=your_key
  Or add to .env file

Problem: Rate limit exceeded
Solution:
  Add delay between requests
  import time
  time.sleep(2)

Problem: Timeout errors
Solution:
  Use faster model
  Reduce max_tokens
  Check network connection

Problem: Poor response quality
Solution:
  Use kilo-quality model
  Improve your prompt
  Increase temperature for creativity
  Add better system_prompt
"""

# ============================================================================
# 15. EXAMPLE REAL WORLD USE CASES
# ============================================================================

"""
1. Customer Support Chatbot
   → Use kilo-fast for quick responses
   → Stream responses to user
   → Cache common questions

2. Content Generation
   → Use kilo-quality for better writing
   → Use system_prompt for brand voice
   → Batch process multiple requests

3. Code Assistant
   → Use kilo-code model
   → Stream code to IDE
   → Handle syntax highlighting

4. Data Analysis
   → Use kilo-reasoning for insights
   → Send CSV summaries
   → Get structured analysis

5. Personal Assistant
   → Use kilo-balanced
   → Remember conversation context
   → Multi-turn conversations
   
6. API Backend
   → Wrap Kilo in FastAPI
   → Add authentication
   → Rate limit per user
   → Log all requests
"""

print("See kilo_advanced.py for full API documentation")
