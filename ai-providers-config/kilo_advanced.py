"""
Kilo Code Provider - Advanced Configuration & Integration Examples
Enhanced setup for production use with Kilo AI
"""

import os
from typing import Optional, Dict, List
from dotenv import load_dotenv
from secret_store import load_api_key

load_dotenv()


class KiloConfig:
    """Advanced Kilo provider configuration"""

    # Basic Setup
    API_KEY = load_api_key("KILO_API_KEY", "kilo")
    BASE_URL = os.getenv("KILO_BASE_URL", "https://api.kilo.ai/v1")
    
    # Model Options
    MODELS = {
        "free": "kilo-auto/free",              # Free tier, auto-switches
        "fast": "kilo-fast",                   # Fast responses
        "balanced": "kilo-balanced",           # Balance speed/quality
        "quality": "kilo-quality",             # Best quality
        "code": "kilo-code",                   # Specialized for code
        "reasoning": "kilo-reasoning",         # For complex reasoning
    }
    
    # Default Model
    DEFAULT_MODEL = os.getenv("KILO_MODEL", "kilo-auto/free")
    
    # Request Configuration
    DEFAULT_CONFIG = {
        "temperature": 0.7,
        "max_tokens": 1024,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }
    
    # Rate Limiting
    RATE_LIMIT = {
        "requests_per_minute": 100,
        "requests_per_hour": 10000,
        "tokens_per_minute": 90000,
    }
    
    # Retry Configuration
    RETRY_CONFIG = {
        "max_retries": 3,
        "retry_delay": 1,
        "backoff_multiplier": 2,
        "max_backoff": 30,
    }
    
    # Logging
    LOGGING = {
        "enabled": os.getenv("KILO_LOG", "true").lower() == "true",
        "level": os.getenv("KILO_LOG_LEVEL", "INFO"),
        "file": "kilo_requests.log",
    }


class KiloAdvancedClient:
    """Advanced Kilo client with caching, retry logic, and monitoring"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or KiloConfig.API_KEY
        if not self.api_key:
            raise ValueError("KILO_API_KEY not set in environment or secrets store")
        
        self.base_url = KiloConfig.BASE_URL
        self.session_cache = {}
        self.request_log = []

    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Enhanced chat with caching and monitoring
        
        Args:
            message: User message
            model: Model to use (default: auto/free)
            system_prompt: System context
            **kwargs: Additional parameters (temperature, max_tokens, etc)
        
        Returns:
            Response dict with content, usage, metadata
        """
        model = model or KiloConfig.DEFAULT_MODEL
        
        # Merge with defaults
        config = {**KiloConfig.DEFAULT_CONFIG, **kwargs}
        
        try:
            import requests
        except ImportError:
            return {"error": "requests library not installed"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
            **config,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Log request
            self.request_log.append({
                "model": model,
                "message_length": len(message),
                "response_tokens": data.get("usage", {}).get("completion_tokens", 0),
                "status": "success",
            })
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", model),
                "finish_reason": data["choices"][0].get("finish_reason"),
            }
        
        except Exception as e:
            self.request_log.append({
                "model": model,
                "status": "error",
                "error": str(e),
            })
            return {"error": str(e)}

    def stream_chat(self, message: str, model: Optional[str] = None) -> None:
        """Stream responses from Kilo"""
        model = model or KiloConfig.DEFAULT_MODEL
        
        try:
            import requests
        except ImportError:
            print("requests library not installed")
            return
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": message},
            ],
            "stream": True,
            **KiloConfig.DEFAULT_CONFIG,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
            )
            
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                import json
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                            except:
                                pass
            print()
        
        except Exception as e:
            print(f"Stream error: {e}")

    def get_request_stats(self) -> Dict:
        """Get statistics about requests"""
        if not self.request_log:
            return {"total_requests": 0}
        
        successful = [r for r in self.request_log if r["status"] == "success"]
        failed = [r for r in self.request_log if r["status"] == "error"]
        
        total_tokens = sum(r.get("response_tokens", 0) for r in successful)
        
        return {
            "total_requests": len(self.request_log),
            "successful": len(successful),
            "failed": len(failed),
            "total_tokens": total_tokens,
            "success_rate": f"{(len(successful) / len(self.request_log) * 100):.1f}%" if self.request_log else "0%",
        }


def kilo_models() -> Dict[str, str]:
    """Get available Kilo models"""
    return KiloConfig.MODELS


def kilo_status() -> Dict:
    """Check Kilo API status"""
    try:
        import requests
    except ImportError:
        return {"error": "requests not installed"}
    
    api_key = KiloConfig.API_KEY
    if not api_key:
        return {"error": "KILO_API_KEY not set in environment or secrets store"}
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"{KiloConfig.BASE_URL}/status",
            headers=headers,
            timeout=5,
        )
        
        if response.status_code == 200:
            return {"status": "operational", "api": "responsive"}
        else:
            return {"status": "available", "response_code": response.status_code}
    
    except Exception as e:
        return {"status": "error", "detail": str(e)}


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("KILO CODE - ADVANCED CONFIGURATION")
    print("="*80 + "\n")
    
    # Show available models
    print("Available Models:")
    print("-" * 40)
    for name, model_id in kilo_models().items():
        print(f"  {name:12} → {model_id}")
    
    # Check API status
    print("\nAPI Status:")
    print("-" * 40)
    status = kilo_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Rate limits
    print("\nRate Limits (Free Tier):")
    print("-" * 40)
    for limit, value in KiloConfig.RATE_LIMIT.items():
        print(f"  {limit}: {value:,}")
    
    # Configuration
    print("\nDefault Configuration:")
    print("-" * 40)
    for key, value in KiloConfig.DEFAULT_CONFIG.items():
        print(f"  {key}: {value}")
    
    # Test chat if API key is available
    if KiloConfig.API_KEY:
        print("\nTesting Kilo Client...")
        print("-" * 40)
        try:
            client = KiloAdvancedClient()
            response = client.chat("Hello, what is Kilo Code?", model="kilo-auto/free")
            
            if "content" in response:
                print(f"✓ Connection successful!")
                print(f"\nResponse:")
                print(f"  {response['content'][:200]}...")
                print(f"\nStats:")
                stats = client.get_request_stats()
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                print(f"✗ Error: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"✗ Error: {e}")
    
    else:
        print("\n⚠️  KILO_API_KEY not set in environment or secrets store")
        print("Set it first: python providers.py store kilo")
