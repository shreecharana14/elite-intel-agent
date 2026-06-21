"""
LLM Provider Abstraction: Support Gemini, Claude, OpenAI with fallback.

Usage:
    provider = LLMProvider(os.getenv("LLM_PROVIDER"))
    brief = provider.synthesize(elite_items)
"""

import os
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv(".env.gemini")


class LLMProvider:
    """Abstract interface for LLM providers."""
    
    def synthesize(self, elite_items: List[Dict]) -> Optional[str]:
        """Turn scored items into a brief."""
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini 2.0 Flash (FREE tier: 15K req/day)."""
    
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            logger.info(f"✅ Gemini provider initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Gemini initialization failed: {e}")
            raise
    
    def synthesize(self, elite_items: List[Dict]) -> Optional[str]:
        """Call Gemini API to generate brief."""
        try:
            import google.generativeai as genai
        except ImportError:
            logger.error("Install google-generativeai: pip install google-generativeai")
            return None
        
        items_text = "\n\n".join([
            f"ITEM {i+1} [Score: {item['composite_score']}]\n"
            f"Title: {item['title']}\n"
            f"Source: {item['source']}\n"
            f"Summary: {item['summary']}\n"
            f"URL: {item['url']}"
            for i, item in enumerate(elite_items)
        ])
        
        prompt = f"""You are an elite intelligence analyst. Write a concise, actionable brief.

Top signals (already scored and filtered):

{items_text}

Brief format:
- 250-350 words
- Use emoji for visual scanning (🔴 critical, 🟠 high, 🟡 watch)
- Include cross-domain connections
- End with 2-3 decision triggers
- Write directly (no preamble)

Brief:
"""
        
        try:
            start = time.time()
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            latency = time.time() - start
            
            logger.info(f"✅ Gemini response in {latency:.3f}s (FREE TIER)")
            return response.text
        except Exception as e:
            logger.error(f"❌ Gemini API failed: {e}")
            return None


class ClaudeProvider(LLMProvider):
    """Anthropic Claude 3.5 Sonnet ($3/1M input tokens)."""
    
    def __init__(self):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
            self.model = "claude-3-5-sonnet-20241022"
            logger.info(f"✅ Claude provider initialized: {self.model}")
        except Exception as e:
            logger.error(f"❌ Claude initialization failed: {e}")
            raise
    
    def synthesize(self, elite_items: List[Dict]) -> Optional[str]:
        """Call Claude API to generate brief."""
        items_text = "\n\n".join([
            f"ITEM {i+1} [Score: {item['composite_score']}]\n"
            f"Title: {item['title']}\n"
            f"Source: {item['source']}\n"
            f"Summary: {item['summary']}\n"
            f"URL: {item['url']}"
            for i, item in enumerate(elite_items)
        ])
        
        prompt = f"""You are an elite intelligence analyst. Write a concise, actionable brief.

Top signals (already scored and filtered):

{items_text}

Brief format:
- 250-350 words
- Use emoji for visual scanning
- Include cross-domain connections
- End with decision triggers

Write the brief directly:"""
        
        try:
            start = time.time()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            latency = time.time() - start
            
            logger.info(f"✅ Claude response in {latency:.3f}s")
            return response.content[0].text
        except Exception as e:
            logger.error(f"❌ Claude API failed: {e}")
            return None


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 Turbo ($0.01/1K input tokens)."""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo"
            logger.info(f"✅ OpenAI provider initialized: {self.model}")
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            raise
    
    def synthesize(self, elite_items: List[Dict]) -> Optional[str]:
        """Call OpenAI API to generate brief."""
        items_text = "\n\n".join([
            f"ITEM {i+1} [Score: {item['composite_score']}]\n"
            f"Title: {item['title']}\n"
            f"Source: {item['source']}\n"
            f"Summary: {item['summary']}\n"
            f"URL: {item['url']}"
            for i, item in enumerate(elite_items)
        ])
        
        prompt = f"""You are an elite intelligence analyst. Write a concise, actionable brief.

Top signals (already scored and filtered):

{items_text}

Brief format:
- 250-350 words
- Use emoji for visual scanning
- Include cross-domain connections
- End with decision triggers

Write the brief directly:"""
        
        try:
            start = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            latency = time.time() - start
            
            logger.info(f"✅ OpenAI response in {latency:.3f}s")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ OpenAI API failed: {e}")
            return None


def get_provider(provider_name: str = None, fallback_provider: str = None) -> LLMProvider:
    """
    Get an LLM provider by name, with optional fallback.
    
    Args:
        provider_name: 'gemini', 'claude', or 'openai' (defaults to env var)
        fallback_provider: fallback if primary fails
    
    Returns:
        LLMProvider instance
    """
    
    providers = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
    }
    
    provider_name = (provider_name or os.getenv("LLM_PROVIDER", "gemini")).lower()
    fallback_provider = fallback_provider or os.getenv("FALLBACK_PROVIDER")
    
    try:
        Provider = providers.get(provider_name)
        if not Provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        return Provider()
    except Exception as e:
        logger.warning(f"Primary provider {provider_name} failed: {e}")
        
        if fallback_provider:
            fallback_name = fallback_provider.lower()
            try:
                logger.info(f"Trying fallback provider: {fallback_name}")
                FallbackProvider = providers.get(fallback_name)
                if not FallbackProvider:
                    raise ValueError(f"Unknown fallback: {fallback_name}")
                return FallbackProvider()
            except Exception as e2:
                logger.error(f"Fallback provider also failed: {e2}")
                raise
        raise
