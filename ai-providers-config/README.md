# AI Providers Configuration System

A complete multi-provider AI API configuration system supporting 10+ major AI platforms.

## Supported Providers

### Free Tier
- **Gemini** (Google AI) - Free tier + paid options
- **Groq** - Ultra-fast inference, free tier included
- **Hugging Face** - Limited free inference + paid
- **Together AI** - Free tier, OpenAI-compatible
- **Replicate** - Free monthly credits

### Freemium / Mixed
- **Mistral AI** - Free API + paid options
- **OpenRouter** - Free models/limits + paid credits
- **Kilo Code** - Free tier, auto-switching

### Trial / Evaluation
- **Cohere** - Trial keys + paid production

### Paid
- **OpenAI** - Pay-per-token, most popular
- **Anthropic** - Pay-per-token, Claude models

## Quick Start

### 1. Clone/Download and Setup

```bash
cd ai-providers-config
bash setup.sh
```

Or manually:

```bash
# Create a locked local config file and use the secure store for API keys
touch .env
chmod 600 .env
python providers.py store gemini

# Then set up the virtualenv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add Your API Keys

Edit `.env` and add at least one API key:

```bash
# Free option (recommended to start)
GEMINI_API_KEY=your_key_here

# Or paid option
OPENAI_API_KEY=your_key_here
```

If you want a locked local store instead of keeping the key in `.env`, use:

```bash
python providers.py store gemini
```

That stores the key in `secrets/<provider>.key` with owner-only permissions.

### 3. List Providers

```bash
# See all providers
python providers.py all

# See only free tier
python providers.py free-tier

# See only configured (have API keys)
python providers.py configured

# See setup instructions for a provider
python providers.py setup gemini
```

### 4. Test a Provider

```bash
# Chat with Gemini
python client.py chat gemini "What is Python?"

# List configured providers
python client.py list

# Compare responses from all providers
python client.py compare "Explain quantum computing"
```

## File Structure

```
ai-providers-config/
├── providers.py          # Provider registry & utilities
├── client.py             # Unified AI client for all providers
├── .env.example          # Template with all API key fields
├── .env                  # Your actual API keys (create from template)
├── requirements.txt      # Python dependencies
├── setup.sh              # Quick setup script
└── README.md             # This file
```

## API Key Setup Instructions

### Get Free API Keys

**Gemini** (Recommended - best free tier)
```bash
1. Go to https://aistudio.google.com
2. Click "Get API key"
3. Create new API key
4. Copy to .env as GEMINI_API_KEY
```

**Groq** (Super fast, free tier)
```bash
1. Go to https://console.groq.com/keys
2. Create new API key
3. Copy to .env as GROQ_API_KEY
```

**Together AI** (Stable, many models)
```bash
1. Go to https://api.together.xyz/
2. Sign up free
3. Create API key
4. Copy to .env as TOGETHER_API_KEY
```

### Get Paid API Keys (Pay-As-You-Go)

**OpenAI** (Most popular)
```
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Set up billing
4. Copy to .env as OPENAI_API_KEY
```

**Anthropic Claude** (Great for reasoning)
```
1. Go to https://console.anthropic.com
2. Create new API key
3. Set up billing
4. Copy to .env as ANTHROPIC_API_KEY
```

See `providers.py setup <name>` for full instructions for any provider.

## Usage Examples

### Python API

```python
from client import AIClient

# Use default (Gemini)
client = AIClient()
response = client.chat("What is machine learning?")
print(response)

# Use specific provider
client = AIClient("openai")
response = client.chat("Explain neural networks")
print(response)

# With custom parameters
response = client.chat(
    "Write a poem about AI",
    temperature=0.9,
    max_tokens=200
)
print(response)
```

### Command Line

```bash
# Single provider
python client.py chat gemini "Hello, how are you?"

# Compare all providers
python client.py compare "What is artificial intelligence?"

# List configured
python client.py list
```

### Check Provider Status

```bash
# All providers
python providers.py all

# Only free tier (no payment needed)
python providers.py free-tier

# Only providers you have keys for
python providers.py configured

# Only providers without keys
python providers.py unconfigured

# Detailed information
python providers.py all -v
```

## Cost Breakdown

### Completely Free
- Gemini (limited requests/day)
- Groq (limited requests/day)
- Replicate ($5 free monthly)

### Freemium (Some free models)
- OpenRouter (free models + free credits)
- Kilo Code (free tier)
- Together AI (free tier)

### Trial (Temporary free)
- Cohere (trial period)

### Paid (No free tier, pay-as-you-go)
- OpenAI (~$0.01 per 1K tokens for GPT-4 mini)
- Anthropic (~$0.03 per 1K tokens input)

## Environment Variables

```bash
GEMINI_API_KEY=...              # Google Gemini free tier
OPENAI_API_KEY=...              # OpenAI paid
ANTHROPIC_API_KEY=...           # Claude paid
MISTRAL_API_KEY=...             # Mistral free API
GROQ_API_KEY=...                # Groq free tier
COHERE_API_KEY=...              # Cohere trial
HF_TOKEN=...                    # Hugging Face free
OPENROUTER_API_KEY=...          # OpenRouter mixed
KILO_API_KEY=...                # Kilo free tier
TOGETHER_API_KEY=...            # Together AI free
REPLICATE_API_TOKEN=...         # Replicate free monthly

# Optional
DEFAULT_PROVIDER=gemini         # Default provider to use
DEBUG=false                     # Debug logging
```

## Secure Local Storage

- `setup.sh` creates `secrets/` with `700` permissions and locks `.env` to `600`
- `python providers.py store <provider>` writes a key to `secrets/<provider>.key`
- The unified client reads from environment variables first, then from the secure store

## Best Practices

1. **Never commit .env** - It contains secrets
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use .env.example** - Share this template instead
   ```bash
   git add .env.example  # Share this
   git ignore .env       # Don't share this
   ```

3. **Start with free tier** - Test before paying
   ```bash
   # Use Gemini first (free)
   python client.py chat gemini "Test"
   
   # Then move to paid if you need production
   ```

4. **Monitor costs** - Watch your usage on provider dashboards
   - OpenAI: https://platform.openai.com/usage
   - Anthropic: https://console.anthropic.com
   - Google: https://console.cloud.google.com/billing

5. **Use provider limits** - Set request limits
   ```python
   client = AIClient("openai")
   response = client.chat(message, max_tokens=100)  # Limit output
   ```

## Troubleshooting

### "Missing API key" Error
```bash
# Check your .env file
cat .env | grep GEMINI_API_KEY

# Run setup again
python providers.py setup gemini
```

### ImportError for SDK
```bash
# Install missing packages
pip install -r requirements.txt

# Or install specific package
pip install google-generativeai
```

### Rate Limited
```bash
# Add delay between requests
import time
time.sleep(1)  # Wait 1 second

# Or use a provider with higher limits
# Try: Groq, Together AI, or OpenRouter
```

### SSL Certificate Error
```bash
# Use environment variable
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
python client.py chat gemini "Test"
```

## Useful Commands

```bash
# See all available commands
python providers.py

# Get setup instructions for any provider
python providers.py setup kilo
python providers.py setup openai
python providers.py setup anthropic

# Test if keys are configured
python providers.py configured

# See what's available to set up
python providers.py unconfigured

# Filter by cost tier
python providers.py paid       # Paid only
python providers.py free-tier  # Free tier
python providers.py mixed      # Free + Paid

# Chat with different providers
python client.py chat gemini "Your prompt"
python client.py chat openai "Your prompt"
python client.py chat groq "Your prompt"

# Get responses from all configured providers
python client.py compare "Your prompt"

# List all configured providers
python client.py list
```

## Adding More Providers

Edit `providers.py` and add to `PROVIDERS` dict:

```python
"your_provider": ProviderConfig(
    name="Your Provider",
    kind=ProviderKind.FREE_TIER,
    api_key_env="YOUR_PROVIDER_API_KEY",
    base_url="https://api.your-provider.com/v1",
    default_model="model-name",
    api_type="rest",
    notes="Description",
    docs_url="https://docs.your-provider.com",
    setup_instructions="""Your setup steps here"""
),
```

Then add implementation to `client.py`:

```python
def _chat_your_provider(self, message: str, model: str, **kwargs) -> str:
    # Your implementation here
    pass
```

## Performance Comparison

| Provider | Speed | Free Tier | Best For |
|----------|-------|-----------|----------|
| Gemini | Fast | ✓ | General use, free tier |
| Groq | Fastest | ✓ | Real-time apps |
| OpenAI | Good | ✗ | Production, best quality |
| Anthropic | Good | ✗ | Reasoning tasks |
| Mistral | Good | (API free) | European alternative |
| Together | Good | ✓ | Open source models |

## Support & Documentation

- **Gemini Docs**: https://ai.google.dev/
- **OpenAI Docs**: https://platform.openai.com/docs
- **Anthropic Docs**: https://docs.anthropic.com
- **Mistral Docs**: https://docs.mistral.ai
- **Groq Docs**: https://console.groq.com/docs
- **Kilo Docs**: https://docs.kilo.ai

## License

MIT - Use freely

---

**Version**: 1.0.0  
**Last Updated**: March 31, 2026  
**Maintainer**: AI Provider Config Team
