"""
Kilo Code Integrations
Examples of integrating Kilo with other tools and services
"""

from secret_store import load_api_key

# ============================================================================
# 1. LANGCHAIN INTEGRATION
# ============================================================================

def setup_langchain_with_kilo():
    """Setup LangChain with Kilo provider"""
    try:
        from langchain_openai import ChatOpenAI
        import os
        
        # Kilo is OpenAI-compatible
        kilo_chat = ChatOpenAI(
            api_key=load_api_key("KILO_API_KEY", "kilo"),
            base_url="https://api.kilo.ai/v1",
            model="kilo-auto/free",
            temperature=0.7,
        )
        
        return kilo_chat
    except ImportError:
        print("Install: pip install langchain langchain-openai")
        return None


# ============================================================================
# 2. LLAMA_INDEX INTEGRATION
# ============================================================================

def setup_llamaindex_with_kilo():
    """Setup LlamaIndex with Kilo"""
    try:
        from llama_index.llms.openai import OpenAI
        import os
        
        kilo_llm = OpenAI(
            api_key=load_api_key("KILO_API_KEY", "kilo"),
            api_base="https://api.kilo.ai/v1",
            model="kilo-auto/free",
        )
        
        return kilo_llm
    except ImportError:
        print("Install: pip install llama-index llama-index-llms-openai")
        return None


# ============================================================================
# 3. DISCORD BOT WITH KILO
# ============================================================================

def discord_bot_example():
    """Discord bot using Kilo for responses"""
    code = '''
import discord
from discord.ext import commands
import os
import requests

# Setup bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

KILO_API_KEY = os.getenv("KILO_API_KEY")
KILO_URL = "https://api.kilo.ai/v1"

@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")

@bot.command(name="ask")
async def ask_kilo(ctx, *, question):
    """Ask Kilo AI a question"""
    async with ctx.typing():
        try:
            headers = {"Authorization": f"Bearer {KILO_API_KEY}"}
            payload = {
                "model": "kilo-auto/free",
                "messages": [{"role": "user", "content": question}],
            }
            
            response = requests.post(
                f"{KILO_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            
            # Split long responses
            if len(answer) > 2000:
                for chunk in [answer[i:i+2000] for i in range(0, len(answer), 2000)]:
                    await ctx.send(chunk)
            else:
                await ctx.send(answer)
        
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

bot.run(os.getenv("DISCORD_TOKEN"))
    '''
    return code


# ============================================================================
# 4. TELEGRAM BOT WITH KILO
# ============================================================================

def telegram_bot_example():
    """Telegram bot using Kilo"""
    code = '''
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import requests

KILO_API_KEY = os.getenv("KILO_API_KEY")
KILO_URL = "https://api.kilo.ai/v1"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me any message and I'll respond with Kilo AI.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        headers = {"Authorization": f"Bearer {KILO_API_KEY}"}
        payload = {
            "model": "kilo-auto/free",
            "messages": [{"role": "user", "content": user_message}],
        }
        
        response = requests.post(
            f"{KILO_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        
        await update.message.reply_text(answer)
    
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    app.run_polling()

if __name__ == "__main__":
    main()
    '''
    return code


# ============================================================================
# 5. SLACK BOT WITH KILO
# ============================================================================

def slack_bot_example():
    """Slack bot using Kilo"""
    code = '''
import os
from slack_bolt import App
import requests

app = App(token=os.getenv("SLACK_BOT_TOKEN"), 
          signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

KILO_API_KEY = os.getenv("KILO_API_KEY")
KILO_URL = "https://api.kilo.ai/v1"

@app.event("app_mention")
def handle_mention(body, logger):
    text = body["event"]["text"]
    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]
    
    # Remove bot mention
    question = text.split(">", 1)[1].strip() if ">" in text else text
    
    try:
        headers = {"Authorization": f"Bearer {KILO_API_KEY}"}
        payload = {
            "model": "kilo-auto/free",
            "messages": [{"role": "user", "content": question}],
        }
        
        response = requests.post(
            f"{KILO_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        
        app.client.chat_postMessage(
            channel=channel_id,
            thread_ts=body["event"]["ts"],
            text=f"<@{user_id}> {answer}"
        )
    
    except Exception as e:
        app.client.chat_postMessage(
            channel=channel_id,
            thread_ts=body["event"]["ts"],
            text=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    app.start(port=int(os.getenv("PORT", 3000)))
    '''
    return code


# ============================================================================
# 6. FASTAPI WITH KILO
# ============================================================================

def fastapi_example():
    """FastAPI backend with Kilo"""
    code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from typing import Optional

app = FastAPI()

KILO_API_KEY = os.getenv("KILO_API_KEY")
KILO_URL = "https://api.kilo.ai/v1"

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "kilo-auto/free"
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_used: int

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint powered by Kilo"""
    try:
        headers = {"Authorization": f"Bearer {KILO_API_KEY}"}
        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.message}],
            "temperature": request.temperature,
        }
        
        response = requests.post(
            f"{KILO_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        return ChatResponse(
            response=data["choices"][0]["message"]["content"],
            model=data["model"],
            tokens_used=data["usage"]["total_tokens"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List available Kilo models"""
    return {
        "models": [
            "kilo-auto/free",
            "kilo-fast",
            "kilo-balanced",
            "kilo-quality",
            "kilo-code",
            "kilo-reasoning",
        ]
    }

# Run with: uvicorn app:app --reload
    '''
    return code


# ============================================================================
# 7. DATA ANALYSIS WITH KILO
# ============================================================================

def data_analysis_example():
    """Data analysis using Kilo"""
    code = '''
import pandas as pd
from kilo_advanced import KiloAdvancedClient

# Load your data
df = pd.read_csv("data.csv")

# Initialize Kilo client
client = KiloAdvancedClient()

# Analyze data
summary = df.describe().to_string()

prompt = f"""
Analyze this data and provide insights:

{summary}

Please provide:
1. Key statistics
2. Trends or patterns
3. Recommendations
"""

response = client.chat(prompt, model="kilo-reasoning")
print(response["content"])
    '''
    return code


# ============================================================================
# 8. DOCUMENT Q&A WITH KILO
# ============================================================================

def document_qa_example():
    """Document Q&A using Kilo"""
    code = '''
from kilo_advanced import KiloAdvancedClient

client = KiloAdvancedClient()

# Read document
with open("document.txt", "r") as f:
    document = f.read()

# Q&A
questions = [
    "Summarize this document",
    "What are the main points?",
    "What action items are mentioned?"
]

for question in questions:
    prompt = f"""
Document:
{document}

Question: {question}
"""
    response = client.chat(prompt)
    print(f"Q: {question}")
    print(f"A: {response['content'][:300]}...")
    print()
    '''
    return code


# ============================================================================
# 9. CODE GENERATION WITH KILO
# ============================================================================

def code_generation_example():
    """Code generation using Kilo"""
    code = '''
from kilo_advanced import KiloAdvancedClient

client = KiloAdvancedClient()

prompt = """
Generate Python code to:
1. Read a CSV file
2. Calculate average of a column
3. Plot results
  
Use pandas and matplotlib.
"""

response = client.chat(prompt, model="kilo-code")
print(response["content"])
    '''
    return code


# ============================================================================
# EXAMPLE SETUP INSTRUCTIONS
# ============================================================================

INTEGRATION_EXAMPLES = {
    "langchain": {
        "description": "Use Kilo with LangChain",
        "install": "pip install langchain langchain-openai",
        "example": setup_langchain_with_kilo,
    },
    "llamaindex": {
        "description": "Use Kilo with LlamaIndex",
        "install": "pip install llama-index llama-index-llms-openai",
        "example": setup_llamaindex_with_kilo,
    },
    "discord": {
        "description": "Discord bot with Kilo",
        "install": "pip install discord.py requests",
        "example": discord_bot_example,
    },
    "telegram": {
        "description": "Telegram bot with Kilo",
        "install": "pip install python-telegram-bot requests",
        "example": telegram_bot_example,
    },
    "slack": {
        "description": "Slack bot with Kilo",
        "install": "pip install slack-bolt requests",
        "example": slack_bot_example,
    },
    "fastapi": {
        "description": "FastAPI backend with Kilo",
        "install": "pip install fastapi uvicorn requests",
        "example": fastapi_example,
    },
    "data_analysis": {
        "description": "Data analysis with Kilo",
        "install": "pip install pandas",
        "example": data_analysis_example,
    },
    "doc_qa": {
        "description": "Document Q&A with Kilo",
        "install": "pip install python-dotenv",
        "example": document_qa_example,
    },
    "code_gen": {
        "description": "Code generation with Kilo",
        "install": "pip install python-dotenv",
        "example": code_generation_example,
    },
}


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("KILO CODE - INTEGRATION EXAMPLES")
    print("="*80 + "\n")
    
    if len(sys.argv) > 1:
        integration = sys.argv[1].lower()
        if integration in INTEGRATION_EXAMPLES:
            example = INTEGRATION_EXAMPLES[integration]
            print(f"Integration: {example['description']}")
            print(f"Install: {example['install']}")
            print("\nExample Code:")
            print("-" * 80)
            print(example['example']())
        else:
            print(f"Unknown integration: {integration}")
            print(f"Available: {', '.join(INTEGRATION_EXAMPLES.keys())}")
    else:
        print("Available Integrations:")
        print("-" * 80)
        for name, example in INTEGRATION_EXAMPLES.items():
            print(f"  {name:15} - {example['description']}")
        
        print("\nTo see example:")
        print("  python kilo_integrations.py <integration>")
        print("\nExamples:")
        print("  python kilo_integrations.py langchain")
        print("  python kilo_integrations.py discord")
        print("  python kilo_integrations.py fastapi")
