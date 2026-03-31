"""
AI Provider Registry - manage all AI API providers in one place
Supports: Gemini, OpenAI, Anthropic, Mistral, Groq, Cohere, HuggingFace, OpenRouter, Kilo
"""

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

from secret_store import ensure_secrets_dir, load_api_key, secret_path, write_secret


class ProviderKind(Enum):
    """Provider cost categories"""
    FREE = "free"
    FREE_TIER = "free_tier"
    TRIAL = "trial"
    PAID = "paid"
    MIXED = "mixed"  # Both free and paid options


@dataclass
class ProviderConfig:
    """Single provider configuration"""
    name: str
    kind: ProviderKind
    api_key_env: str
    base_url: str
    default_model: str
    sdk_module: Optional[str] = None  # Python SDK module name
    api_type: str = "rest"  # "rest" or "sdk"
    notes: str = ""
    docs_url: str = ""
    enabled: bool = True
    setup_instructions: str = ""
    secret_name: Optional[str] = None

    def api_key(self) -> Optional[str]:
        """Get API key from environment or secure local storage."""
        return load_api_key(self.api_key_env, self.secret_storage_name())

    def secret_storage_name(self) -> str:
        """Return the local secret filename stem for this provider."""
        return self.secret_name or self.api_key_env.lower()

    def secret_file(self) -> Path:
        """Return the path used for this provider's secure storage."""
        return secret_path(self.secret_storage_name())

    def is_configured(self) -> bool:
        """Check if API key is set"""
        return bool(self.api_key())

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "kind": self.kind.value,
            "configured": self.is_configured(),
            "model": self.default_model,
            "base_url": self.base_url,
            "api_type": self.api_type,
            "notes": self.notes,
        }


# Provider Registry - All major AI APIs
PROVIDERS: Dict[str, ProviderConfig] = {
    "gemini": ProviderConfig(
        name="Gemini",
        kind=ProviderKind.FREE_TIER,
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com",
        default_model="gemini-2.5-flash",
        sdk_module="google.generativeai",
        api_type="sdk",
        notes="Free tier + paid options",
        docs_url="https://ai.google.dev/",
        setup_instructions="""
1. Go to https://aistudio.google.com
2. Click 'Get API key'
3. Create new API key
4. Copy and save to .env as GEMINI_API_KEY
        """
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        kind=ProviderKind.PAID,
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4.1-mini",
        sdk_module="openai",
        api_type="sdk",
        notes="Paid API - pay per token",
        docs_url="https://platform.openai.com/docs/",
        setup_instructions="""
1. Go to https://platform.openai.com/account/api-keys
2. Create new API key
3. Copy and save to .env as OPENAI_API_KEY
4. Set up billing
        """
    ),
    "anthropic": ProviderConfig(
        name="Anthropic (Claude)",
        kind=ProviderKind.PAID,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com",
        default_model="claude-opus-4-1",
        sdk_module="anthropic",
        api_type="sdk",
        notes="Paid API - Claude models",
        docs_url="https://docs.anthropic.com/",
        setup_instructions="""
1. Go to https://console.anthropic.com/account/keys
2. Create new API key
3. Copy and save to .env as ANTHROPIC_API_KEY
4. Set up billing
        """
    ),
    "mistral": ProviderConfig(
        name="Mistral AI",
        kind=ProviderKind.MIXED,
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        default_model="mistral-small-latest",
        sdk_module="mistralai",
        api_type="sdk",
        notes="Free API access + paid options",
        docs_url="https://docs.mistral.ai/",
        setup_instructions="""
1. Go to https://console.mistral.ai/api-keys/
2. Create new API key
3. Copy and save to .env as MISTRAL_API_KEY
        """
    ),
    "groq": ProviderConfig(
        name="Groq",
        kind=ProviderKind.FREE_TIER,
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        sdk_module="groq",
        api_type="sdk",
        notes="Free tier + paid developer plan",
        docs_url="https://console.groq.com/docs/",
        setup_instructions="""
1. Go to https://console.groq.com/keys
2. Create new API key
3. Copy and save to .env as GROQ_API_KEY
4. Free tier available
        """
    ),
    "cohere": ProviderConfig(
        name="Cohere",
        kind=ProviderKind.TRIAL,
        api_key_env="COHERE_API_KEY",
        base_url="https://api.cohere.com/v2",
        default_model="command-r-plus",
        sdk_module="cohere",
        api_type="sdk",
        notes="Trial/evaluation keys + paid production",
        docs_url="https://docs.cohere.com/",
        setup_instructions="""
1. Go to https://api.cohere.com/dashboard/api-keys
2. Create new API key (trial available)
3. Copy and save to .env as COHERE_API_KEY
        """
    ),
    "huggingface": ProviderConfig(
        name="Hugging Face",
        kind=ProviderKind.FREE_TIER,
        api_key_env="HF_TOKEN",
        base_url="https://router.huggingface.co/v1",
        default_model="HuggingFaceH4/zephyr-7b-beta",
        sdk_module="huggingface_hub",
        api_type="rest",
        notes="Limited free inference + paid endpoints",
        docs_url="https://huggingface.co/docs/hub/security-tokens",
        setup_instructions="""
1. Go to https://huggingface.co/settings/tokens
2. Create new token (read)
3. Copy and save to .env as HF_TOKEN
        """
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        kind=ProviderKind.MIXED,
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        default_model="openrouter/free",
        api_type="rest",
        notes="Free models/limits + paid credits",
        docs_url="https://openrouter.ai/docs",
        setup_instructions="""
1. Go to https://openrouter.ai/keys
2. Create new API key
3. Copy and save to .env as OPENROUTER_API_KEY
4. Free credits included
        """
    ),
    "kilo": ProviderConfig(
        name="Kilo Code",
        kind=ProviderKind.FREE_TIER,
        api_key_env="KILO_API_KEY",
        base_url="https://api.kilo.ai/v1",
        default_model="kilo-auto/free",
        api_type="rest",
        notes="Free tier for development, supports auto-switching",
        docs_url="https://docs.kilo.ai/",
        setup_instructions="""
1. Go to https://kilo.ai/dashboard
2. Navigate to API Keys
3. Create new API key
4. Copy and save to .env as KILO_API_KEY
5. Use 'kilo-auto/free' for auto model switching
        """
    ),
    "together": ProviderConfig(
        name="Together AI",
        kind=ProviderKind.FREE_TIER,
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
        default_model="meta-llama/Llama-3-70b-chat",
        api_type="rest",
        notes="Free tier available, OpenAI-compatible",
        docs_url="https://www.together.ai/docs",
        setup_instructions="""
1. Go to https://api.together.xyz/
2. Sign up for free
3. Navigate to Settings → API Keys
4. Create new key
5. Save to .env as TOGETHER_API_KEY
        """
    ),
    "replicate": ProviderConfig(
        name="Replicate",
        kind=ProviderKind.FREE_TIER,
        api_key_env="REPLICATE_API_TOKEN",
        base_url="https://api.replicate.com/v1",
        default_model="meta/llama-2-70b-chat",
        api_type="rest",
        notes="Pay-per-inference model, free tier available",
        docs_url="https://replicate.com/docs",
        setup_instructions="""
1. Go to https://replicate.com/account/api-tokens
2. Create new token
3. Save to .env as REPLICATE_API_TOKEN
4. Free month credits included
        """
    ),
}

for provider_key, provider in PROVIDERS.items():
    if not provider.secret_name:
        provider.secret_name = provider_key


def get_provider(name: str) -> Optional[ProviderConfig]:
    """Get provider by name"""
    return PROVIDERS.get(name.lower())


def list_providers(kind: Optional[ProviderKind] = None) -> List[ProviderConfig]:
    """List all providers, optionally filtered by kind"""
    items = list(PROVIDERS.values())
    if kind:
        items = [p for p in items if p.kind == kind]
    return sorted(items, key=lambda p: p.name)


def configured_providers() -> List[ProviderConfig]:
    """List only providers with API keys set"""
    return [p for p in PROVIDERS.values() if p.is_configured()]


def unconfigured_providers() -> List[ProviderConfig]:
    """List providers without API keys"""
    return [p for p in PROVIDERS.values() if not p.is_configured()]


def print_table(items: List[ProviderConfig], verbose: bool = False) -> None:
    """Pretty print provider table"""
    if not items:
        print("No providers found")
        return

    headers = ["Provider", "Status", "Type", "Model", "Default"]
    rows = []

    for p in items:
        status = "✓ Configured" if p.is_configured() else "✗ Missing Key"
        default = "Yes" if p.is_configured() else "-"
        rows.append([
            p.name,
            status,
            p.kind.value,
            p.api_type.upper(),
            default,
        ])

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-+-".join("-" * w for w in widths))

    # Print rows
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))

    if verbose:
        print("\n" + "=" * 80)
        for p in items:
            print(f"\n{p.name.upper()}")
            print(f"  API Key Env: {p.api_key_env}")
            print(f"  Base URL: {p.base_url}")
            print(f"  Default Model: {p.default_model}")
            print(f"  Documentation: {p.docs_url}")
            print(f"  Notes: {p.notes}")


def export_config() -> dict:
    """Export all provider configs as dictionary"""
    return {
        "total": len(PROVIDERS),
        "configured": len(configured_providers()),
        "providers": {name: p.to_dict() for name, p in PROVIDERS.items()}
    }


def store_provider_key(provider_name: str, api_key: str, overwrite: bool = False) -> Path:
    """Store a provider API key in the local secure secrets directory."""
    provider = get_provider(provider_name)
    if not provider:
        raise ValueError(f"Unknown provider: {provider_name}")

    ensure_secrets_dir()
    return write_secret(provider.secret_storage_name(), api_key, overwrite=overwrite)


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    print(f"\n{'='*80}")
    print(f"AI PROVIDER REGISTRY - {mode.upper()}")
    print(f"{'='*80}\n")

    if mode == "all":
        items = list_providers()
        print(f"All Providers ({len(items)}):\n")
    elif mode == "free":
        items = list_providers(ProviderKind.FREE)
        print(f"Free Providers ({len(items)}):\n")
    elif mode == "free-tier" or mode == "freetier":
        items = list_providers(ProviderKind.FREE_TIER)
        print(f"Free Tier Providers ({len(items)}):\n")
    elif mode == "paid":
        items = list_providers(ProviderKind.PAID)
        print(f"Paid Providers ({len(items)}):\n")
    elif mode == "mixed":
        items = list_providers(ProviderKind.MIXED)
        print(f"Mixed (Free + Paid) Providers ({len(items)}):\n")
    elif mode == "configured":
        items = configured_providers()
        print(f"Configured Providers ({len(items)}):\n")
    elif mode == "unconfigured":
        items = unconfigured_providers()
        print(f"Unconfigured Providers ({len(items)}):\n")
    elif mode == "setup":
        # Show setup instructions
        if len(sys.argv) > 2:
            provider_name = sys.argv[2].lower()
            p = get_provider(provider_name)
            if p:
                print(f"\nSETUP: {p.name}")
                print("="*80)
                print(p.setup_instructions)
                print(f"\nDocumentation: {p.docs_url}\n")
            else:
                print(f"Provider '{provider_name}' not found")
                print(f"Available: {', '.join(sorted(PROVIDERS.keys()))}")
        else:
            print("Usage: python providers.py setup <provider_name>")
            print(f"Available: {', '.join(sorted(PROVIDERS.keys()))}")
    elif mode == "store":
        if len(sys.argv) < 3:
            print("Usage: python providers.py store <provider_name> [api_key]")
            print("If api_key is omitted, you will be prompted securely.")
            print(f"Available: {', '.join(sorted(PROVIDERS.keys()))}")
            exit(1)

        provider_name = sys.argv[2].lower()
        provider = get_provider(provider_name)
        if not provider:
            print(f"Provider '{provider_name}' not found")
            print(f"Available: {', '.join(sorted(PROVIDERS.keys()))}")
            exit(1)

        if len(sys.argv) > 3:
            api_key = sys.argv[3]
        else:
            api_key = getpass(f"Enter API key for {provider.name}: ")

        overwrite = "--overwrite" in sys.argv or "-f" in sys.argv
        path = store_provider_key(provider_name, api_key, overwrite=overwrite)
        print(f"Stored securely in {path}")
    else:
        print(f"Unknown mode: {mode}")
        print("\nUsage:")
        print("  python providers.py all          - List all providers")
        print("  python providers.py free         - List free providers")
        print("  python providers.py free-tier    - List free-tier providers")
        print("  python providers.py paid         - List paid providers")
        print("  python providers.py mixed        - List mixed (free+paid) providers")
        print("  python providers.py configured   - List configured providers")
        print("  python providers.py unconfigured - List unconfigured providers")
        print("  python providers.py setup <name> - Show setup instructions")
        print("  python providers.py store <name> - Store an API key securely")
        print("  -v, --verbose                    - Show detailed information")
        exit(1)

    print_table(items, verbose=verbose)
    print()
