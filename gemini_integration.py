#!/usr/bin/env python3
"""
Enhanced Google Gemini Integration Module
Provides comprehensive AI functionality for code completion, chat, and analysis
"""

import asyncio
import json
import subprocess
import time
import threading
from typing import Dict, List, Optional, Callable, AsyncGenerator, Any
from dataclasses import dataclass
from pathlib import Path
import logging
import re

# Try to import google cloud libraries
try:
    from google.cloud import aiplatform
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

@dataclass
class AIRequest:
    """AI request data structure"""
    prompt: str
    context: str = ""
    max_tokens: int = 1024
    temperature: float = 0.7
    stream: bool = False
    request_type: str = "completion"  # completion, chat, analysis
    
@dataclass
class AIResponse:
    """AI response data structure"""
    content: str
    finish_reason: str = "stop"
    usage: Dict[str, int] = None
    model: str = ""
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if self.created_at == 0.0:
            self.created_at = time.time()

class GeminiCLIService:
    """Google Gemini CLI integration service"""
    
    def __init__(self, config_manager=None):
        self.config = config_manager.config if config_manager else None
        self.logger = logging.getLogger(__name__)
        self.authenticated = False
        self.project_id = None
        self.model_name = "gemini-pro"
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        
        # Context management
        self.conversation_history: List[Dict[str, str]] = []
        self.code_context: Dict[str, Any] = {}
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the Gemini service"""
        self.logger.info("Initializing Gemini CLI service...")
        
        if not self._check_gcloud_installation():
            self.logger.error("Google Cloud CLI not found")
            return
        
        self._check_authentication()
        
        if self.config:
            self.project_id = self.config.google_cloud.project_id
            self.model_name = self.config.google_cloud.model_name
    
    def _check_gcloud_installation(self) -> bool:
        """Check if Google Cloud CLI is installed and accessible"""
        try:
            result = subprocess.run(
                ['gcloud', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info("Google Cloud CLI found")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Google Cloud CLI check failed: {e}")
        
        return False
    
    def _check_authentication(self) -> bool:
        """Check Google Cloud authentication status"""
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                accounts = json.loads(result.stdout)
                active_accounts = [acc for acc in accounts if acc.get('status') == 'ACTIVE']
                
                if active_accounts:
                    self.authenticated = True
                    self.logger.info(f"Authenticated as: {active_accounts[0].get('account')}")
                    return True
                else:
                    self.logger.warning("No active Google Cloud authentication found")
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Authentication check failed: {e}")
        
        return False
    
    async def authenticate(self, force_reauth: bool = False) -> bool:
        """Authenticate with Google Cloud"""
        if self.authenticated and not force_reauth:
            return True
        
        try:
            if force_reauth:
                # Force re-authentication
                process = await asyncio.create_subprocess_exec(
                    'gcloud', 'auth', 'login', '--force',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Check if we can use existing auth
                process = await asyncio.create_subprocess_exec(
                    'gcloud', 'auth', 'application-default', 'login',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.authenticated = True
                self.logger.info("Successfully authenticated with Google Cloud")
                return True
            else:
                self.logger.error(f"Authentication failed: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
        
        return False
    
    async def generate_completion(self, request: AIRequest) -> AIResponse:
        """Generate code completion using Gemini"""
        if not self.authenticated:
            return AIResponse(
                content="// Please authenticate with Google Cloud first",
                finish_reason="error"
            )
        
        await self.rate_limiter.wait_if_needed()
        
        try:
            # Build the completion prompt
            prompt = self._build_completion_prompt(request.prompt, request.context)
            
            # Call Gemini CLI
            if request.stream:
                return await self._stream_completion(prompt, request)
            else:
                return await self._batch_completion(prompt, request)
                
        except Exception as e:
            self.logger.error(f"Completion generation failed: {e}")
            return AIResponse(
                content=f"// Error generating completion: {str(e)}",
                finish_reason="error"
            )
    
    async def _batch_completion(self, prompt: str, request: AIRequest) -> AIResponse:
        """Generate batch completion"""
        cmd = [
            'gcloud', 'ai', 'models', 'predict',
            '--model', self.model_name,
            '--json-request', '-'
        ]
        
        # Prepare request payload
        payload = {
            "instances": [{
                "content": prompt
            }],
            "parameters": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
                "topK": 40,
                "topP": 0.95
            }
        }
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(
                input=json.dumps(payload).encode()
            )
            
            if process.returncode == 0:
                response_data = json.loads(stdout.decode())
                content = self._extract_content_from_response(response_data)
                
                return AIResponse(
                    content=content,
                    finish_reason="stop",
                    model=self.model_name
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Gemini API error: {error_msg}")
                return AIResponse(
                    content=f"// API Error: {error_msg}",
                    finish_reason="error"
                )
                
        except Exception as e:
            self.logger.error(f"Batch completion error: {e}")
            return AIResponse(
                content=f"// Error: {str(e)}",
                finish_reason="error"
            )
    
    async def _stream_completion(self, prompt: str, request: AIRequest) -> AsyncGenerator[str, None]:
        """Generate streaming completion"""
        # For now, simulate streaming by chunking the batch response
        response = await self._batch_completion(prompt, request)
        
        # Split response into chunks for streaming effect
        words = response.content.split()
        chunk_size = max(1, len(words) // 10)
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            yield chunk
            await asyncio.sleep(0.1)  # Simulate network delay
    
    async def chat_completion(self, message: str, context: str = "") -> AIResponse:
        """Generate chat response"""
        if not self.authenticated:
            return AIResponse(
                content="Please authenticate with Google Cloud first.",
                finish_reason="error"
            )
        
        await self.rate_limiter.wait_if_needed()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Build chat prompt with history
        chat_prompt = self._build_chat_prompt(message, context)
        
        request = AIRequest(
            prompt=chat_prompt,
            context=context,
            max_tokens=2048,
            temperature=0.8,
            request_type="chat"
        )
        
        response = await self._batch_completion(chat_prompt, request)
        
        # Add response to history
        if response.finish_reason != "error":
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def _build_completion_prompt(self, code: str, context: str) -> str:
        """Build prompt for code completion"""
        # Detect programming language
        language = self._detect_language(context)
        
        prompt = f"""You are an expert {language} programmer. Complete the following code intelligently.

Context:
```{language}
{context[-1000:]}  # Last 1000 chars for context
```

Complete this code:
```{language}
{code}"""
        
        return prompt
    
    def _build_chat_prompt(self, message: str, context: str) -> str:
        """Build prompt for chat completion"""
        language = self._detect_language(context)
        
        # Build conversation history
        history_text = ""
        for entry in self.conversation_history[-10:]:  # Last 10 exchanges
            role = entry["role"].capitalize()
            content = entry["content"][:500]  # Truncate long messages
            history_text += f"{role}: {content}\n"
        
        prompt = f"""You are an expert programming assistant. Help with coding questions and provide clear, accurate answers.

Current code context ({language}):
```{language}
{context[-800:] if context else "No code context available"}
```

Conversation history:
{history_text}

User: {message}
Assistant:"""
        
        return prompt
    
    def _detect_language(self, context: str) -> str:
        """Detect programming language from context"""
        if not context:
            return "text"
        
        # Simple language detection based on keywords and patterns
        context_lower = context.lower()
        
        if any(keyword in context_lower for keyword in ['def ', 'import ', 'class ', '__init__', 'self.']):
            return "python"
        elif any(keyword in context_lower for keyword in ['function ', 'var ', 'let ', 'const ', '=>']):
            return "javascript"
        elif any(keyword in context_lower for keyword in ['public class', 'private ', 'public static']):
            return "java"
        elif any(keyword in context_lower for keyword in ['#include', 'int main', 'std::']):
            return "cpp"
        elif any(keyword in context_lower for keyword in ['<html>', '<div>', '<script>']):
            return "html"
        elif any(keyword in context_lower for keyword in ['{', '}', 'margin:', 'padding:']):
            return "css"
        else:
            return "text"
    
    def _extract_content_from_response(self, response_data: Dict) -> str:
        """Extract content from Gemini API response"""
        try:
            # Handle different response formats
            if 'predictions' in response_data:
                predictions = response_data['predictions']
                if predictions and len(predictions) > 0:
                    prediction = predictions[0]
                    
                    # Try different content fields
                    for field in ['content', 'text', 'generated_text', 'output']:
                        if field in prediction:
                            return prediction[field].strip()
            
            # Fallback: convert entire response to string
            return str(response_data)
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            return f"// Error parsing response: {str(e)}"
    
    async def analyze_code(self, code: str, analysis_type: str = "general") -> AIResponse:
        """Analyze code for issues, improvements, etc."""
        analysis_prompts = {
            "general": "Analyze this code for potential issues, improvements, and best practices:",
            "security": "Perform a security analysis of this code, identifying potential vulnerabilities:",
            "performance": "Analyze this code for performance issues and optimization opportunities:",
            "style": "Review this code for style issues and adherence to best practices:",
            "bugs": "Identify potential bugs and logical errors in this code:"
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        full_prompt = f"""{prompt}

```
{code}
```

Provide specific, actionable feedback with examples where possible."""
        
        request = AIRequest(
            prompt=full_prompt,
            max_tokens=1024,
            temperature=0.3,  # Lower temperature for more focused analysis
            request_type="analysis"
        )
        
        return await self._batch_completion(full_prompt, request)
    
    async def generate_documentation(self, code: str, doc_type: str = "docstring") -> AIResponse:
        """Generate documentation for code"""
        language = self._detect_language(code)
        
        doc_prompts = {
            "docstring": f"Generate comprehensive docstrings/comments for this {language} code:",
            "readme": f"Generate a README.md section explaining this {language} code:",
            "api": f"Generate API documentation for this {language} code:",
            "inline": f"Add inline comments to explain this {language} code:"
        }
        
        prompt = doc_prompts.get(doc_type, doc_prompts["docstring"])
        full_prompt = f"""{prompt}

```{language}
{code}
```

Provide clear, comprehensive documentation following {language} conventions."""
        
        request = AIRequest(
            prompt=full_prompt,
            max_tokens=1024,
            temperature=0.4,
            request_type="documentation"
        )
        
        return await self._batch_completion(full_prompt, request)
    
    async def generate_tests(self, code: str, test_framework: str = "auto") -> AIResponse:
        """Generate unit tests for code"""
        language = self._detect_language(code)
        
        # Auto-detect test framework based on language
        if test_framework == "auto":
            framework_map = {
                "python": "pytest",
                "javascript": "jest",
                "java": "junit",
                "cpp": "gtest"
            }
            test_framework = framework_map.get(language, "standard")
        
        prompt = f"""Generate comprehensive unit tests for this {language} code using {test_framework}.

Code to test:
```{language}
{code}
```

Generate tests that cover:
1. Normal functionality
2. Edge cases
3. Error conditions
4. Boundary values

Follow {test_framework} conventions and best practices."""
        
        request = AIRequest(
            prompt=prompt,
            max_tokens=1536,
            temperature=0.3,
            request_type="testing"
        )
        
        return await self._batch_completion(prompt, request)
    
    def clear_conversation_history(self):
        """Clear chat conversation history"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()
    
    def update_code_context(self, file_path: str, content: str):
        """Update code context for better completions"""
        self.code_context[file_path] = {
            "content": content,
            "language": self._detect_language(content),
            "updated_at": time.time()
        }
        
        # Keep only recent contexts (max 10 files)
        if len(self.code_context) > 10:
            # Remove oldest entries
            sorted_contexts = sorted(
                self.code_context.items(),
                key=lambda x: x[1]["updated_at"]
            )
            for old_file, _ in sorted_contexts[:-10]:
                del self.code_context[old_file]

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            self.request_times = [
                req_time for req_time in self.request_times 
                if now - req_time < 60
            ]
            
            # Check if we need to wait
            if len(self.request_times) >= self.requests_per_minute:
                oldest_request = min(self.request_times)
                wait_time = 60 - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self.request_times.append(now)

class AIAssistant:
    """High-level AI assistant interface"""
    
    def __init__(self, config_manager=None):
        self.gemini_service = GeminiCLIService(config_manager)
        self.logger = logging.getLogger(__name__)
        self.completion_cache: Dict[str, AIResponse] = {}
        self.cache_max_size = 100
    
    async def initialize(self):
        """Initialize the AI assistant"""
        self.logger.info("Initializing AI Assistant...")
        
        # Check authentication
        if not await self.gemini_service.authenticate():
            self.logger.warning("AI features may be limited without authentication")
            return False
        
        self.logger.info("AI Assistant initialized successfully")
        return True
    
    async def get_code_completion(self, code: str, context: str = "", 
                                cache_key: Optional[str] = None) -> AIResponse:
        """Get code completion with caching"""
        # Check cache first
        if cache_key and cache_key in self.completion_cache:
            cached_response = self.completion_cache[cache_key]
            # Return cached if less than 5 minutes old
            if time.time() - cached_response.created_at < 300:
                return cached_response
        
        request = AIRequest(
            prompt=code,
            context=context,
            max_tokens=512,
            temperature=0.3,
            request_type="completion"
        )
        
        response = await self.gemini_service.generate_completion(request)
        
        # Cache the response
        if cache_key and response.finish_reason != "error":
            self._add_to_cache(cache_key, response)
        
        return response
    
    async def chat_with_ai(self, message: str, file_context: str = "") -> AIResponse:
        """Chat with AI assistant"""
        return await self.gemini_service.chat_completion(message, file_context)
    
    async def analyze_code_quality(self, code: str) -> AIResponse:
        """Analyze code quality"""
        return await self.gemini_service.analyze_code(code, "general")
    
    async def find_security_issues(self, code: str) -> AIResponse:
        """Find security issues in code"""
        return await self.gemini_service.analyze_code(code, "security")
    
    async def suggest_performance_improvements(self, code: str) -> AIResponse:
        """Suggest performance improvements"""
        return await self.gemini_service.analyze_code(code, "performance")
    
    async def generate_code_documentation(self, code: str) -> AIResponse:
        """Generate documentation for code"""
        return await self.gemini_service.generate_documentation(code)
    
    async def create_unit_tests(self, code: str) -> AIResponse:
        """Create unit tests for code"""
        return await self.gemini_service.generate_tests(code)
    
    def _add_to_cache(self, key: str, response: AIResponse):
        """Add response to cache"""
        if len(self.completion_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_key = min(
                self.completion_cache.keys(),
                key=lambda k: self.completion_cache[k].created_at
            )
            del self.completion_cache[oldest_key]
        
        self.completion_cache[key] = response
    
    def clear_cache(self):
        """Clear completion cache"""
        self.completion_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "authenticated": self.gemini_service.authenticated,
            "cache_size": len(self.completion_cache),
            "conversation_length": len(self.gemini_service.conversation_history),
            "contexts_tracked": len(self.gemini_service.code_context)
        }

# Global AI assistant instance
ai_assistant: Optional[AIAssistant] = None

def get_ai_assistant(config_manager=None) -> AIAssistant:
    """Get global AI assistant instance"""
    global ai_assistant
    if ai_assistant is None:
        ai_assistant = AIAssistant(config_manager)
    return ai_assistant

async def initialize_ai_services(config_manager=None):
    """Initialize AI services"""
    assistant = get_ai_assistant(config_manager)
    return await assistant.initialize()

if __name__ == "__main__":
    # Test the Gemini integration
    async def test_gemini():
        assistant = AIAssistant()
        
        if await assistant.initialize():
            # Test code completion
            completion = await assistant.get_code_completion(
                "def fibonacci(n):",
                "# Python function to calculate fibonacci numbers"
            )
            print("Completion:", completion.content)
            
            # Test chat
            chat_response = await assistant.chat_with_ai(
                "How do I optimize this fibonacci function?",
                "def fibonacci(n):\n    if n <= 1:\n        return n"
            )
            print("Chat:", chat_response.content)
        else:
            print("Failed to initialize AI services")
    
    asyncio.run(test_gemini())