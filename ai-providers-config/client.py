"""
Send prompts to multiple AI providers from a single interface
Supports: Gemini, OpenAI, Anthropic, Mistral, Groq, Cohere, HuggingFace, OpenRouter, Kilo
"""

import os
import sys
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from providers import get_provider, configured_providers

# Load environment variables
load_dotenv()


class AIClient:
    """Unified AI client for multiple providers"""

    def __init__(self, provider_name: str = "gemini"):
        self.provider_config = get_provider(provider_name)
        if not self.provider_config:
            raise ValueError(f"Unknown provider: {provider_name}")

        self.api_key = self.provider_config.api_key()
        if not self.api_key:
            raise ValueError(
                f"Missing API key for {provider_name}. "
                f"Set {self.provider_config.api_key_env} in .env"
            )

    def chat(self, message: str, model: Optional[str] = None, **kwargs) -> str:
        """Send a message and get a response"""
        model = model or self.provider_config.default_model

        if self.provider_config.name == "Gemini":
            return self._chat_gemini(message, model, **kwargs)
        elif self.provider_config.name == "OpenAI":
            return self._chat_openai(message, model, **kwargs)
        elif self.provider_config.name == "Anthropic (Claude)":
            return self._chat_anthropic(message, model, **kwargs)
        elif self.provider_config.name in ["Mistral AI", "Groq", "OpenRouter", "Kilo Code", "Together AI"]:
            return self._chat_openai_compatible(message, model, **kwargs)
        elif self.provider_config.name == "Cohere":
            return self._chat_cohere(message, model, **kwargs)
        elif self.provider_config.name == "Hugging Face":
            return self._chat_huggingface(message, model, **kwargs)
        elif self.provider_config.name == "Replicate":
            return self._chat_replicate(message, model, **kwargs)
        else:
            raise NotImplementedError(f"Provider {self.provider_config.name} not yet implemented")

    def _chat_gemini(self, message: str, model: str, **kwargs) -> str:
        """Chat with Google Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            return "Error: google-generativeai not installed. Run: pip install google-generativeai"

        genai.configure(api_key=self.api_key)
        client = genai.GenerativeModel(model)
        response = client.generate_content(message)
        return response.text

    def _chat_openai(self, message: str, model: str, **kwargs) -> str:
        """Chat with OpenAI"""
        try:
            from openai import OpenAI
        except ImportError:
            return "Error: openai not installed. Run: pip install openai"

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            **kwargs
        )
        return response.choices[0].message.content

    def _chat_anthropic(self, message: str, model: str, **kwargs) -> str:
        """Chat with Anthropic Claude"""
        try:
            from anthropic import Anthropic
        except ImportError:
            return "Error: anthropic not installed. Run: pip install anthropic"

        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": message}],
            **kwargs
        )
        return response.content[0].text

    def _chat_openai_compatible(self, message: str, model: str, **kwargs) -> str:
        """Chat with OpenAI-compatible API (Mistral, Groq, OpenRouter, etc.)"""
        try:
            from openai import OpenAI
        except ImportError:
            return "Error: openai not installed. Run: pip install openai"

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.provider_config.base_url,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
            **kwargs
        )
        return response.choices[0].message.content

    def _chat_cohere(self, message: str, model: str, **kwargs) -> str:
        """Chat with Cohere"""
        try:
            import cohere
        except ImportError:
            return "Error: cohere not installed. Run: pip install cohere"

        client = cohere.ClientV2(api_key=self.api_key)
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": message}],
        )
        return response.message.content[0].text

    def _chat_huggingface(self, message: str, model: str, **kwargs) -> str:
        """Chat with Hugging Face"""
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": message}

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", str(result))
            return str(result)
        else:
            return f"Error: {response.status_code} - {response.text}"

    def _chat_replicate(self, message: str, model: str, **kwargs) -> str:
        """Chat with Replicate"""
        try:
            import replicate
        except ImportError:
            return "Error: replicate not installed. Run: pip install replicate"

        replicate.api_token = self.api_key
        output = replicate.run(model, input={"prompt": message})

        if isinstance(output, list):
            return "".join(output)
        return str(output)


def compare_providers(message: str, providers: Optional[list] = None) -> Dict[str, str]:
    """Compare responses from multiple providers"""
    if not providers:
        providers = [p.name.lower().split()[0] for p in configured_providers()]

    if not providers:
        print("Error: No configured providers found")
        print("Please add API keys to .env")
        return {}

    print(f"\n{'='*80}")
    print(f"COMPARING {len(providers)} PROVIDERS")
    print(f"{'='*80}")
    print(f"Prompt: {message}\n")

    results = {}

    for provider_name in providers:
        print(f"Querying {provider_name.upper()}...", end=" ", flush=True)
        try:
            client = AIClient(provider_name)
            response = client.chat(message, temperature=0.7, max_tokens=150)
            results[provider_name] = response
            print("✓")
        except Exception as e:
            results[provider_name] = f"Error: {str(e)}"
            print("✗")

    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}\n")

    for provider, response in results.items():
        print(f"\n{provider.upper()}:")
        print("-" * 40)
        print(response[:500] + "..." if len(str(response)) > 500 else response)

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "chat":
            if len(sys.argv) < 3:
                print("Usage: python client.py chat <provider> '<message>'")
                print("Example: python client.py chat gemini 'Hello, how are you?'")
                exit(1)

            provider = sys.argv[2]
            message = sys.argv[3] if len(sys.argv) > 3 else input("Message: ")

            try:
                client = AIClient(provider)
                response = client.chat(message)
                print(f"\n{provider.upper()} Response:")
                print("-" * 40)
                print(response)
            except Exception as e:
                print(f"Error: {e}")

        elif command == "compare":
            message = sys.argv[2] if len(sys.argv) > 2 else input("Message: ")
            compare_providers(message)

        elif command == "list":
            print("\nConfigured Providers:")
            for p in configured_providers():
                print(f"  ✓ {p.name}")

        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python client.py chat <provider> '<message>'")
            print("  python client.py compare '<message>'")
            print("  python client.py list")

    else:
        print("Usage:")
        print("  python client.py chat <provider> '<message>'")
        print("  python client.py compare '<message>'")
        print("  python client.py list")
        print("\nExample:")
        print("  python client.py chat gemini 'What is AI?'")
        print("  python client.py compare 'Explain quantum computing'")
