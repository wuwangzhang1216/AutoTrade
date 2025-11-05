"""
OpenRouter API client for AI model access
"""
import json
import time
from typing import Dict, Optional
from openai import OpenAI
from utils.logger import logger, log_error, log_ai
from config import settings, AIDecisionConfig


class OpenRouterClient:
    """
    Client for OpenRouter API
    """

    def __init__(self):
        """Initialize OpenRouter client"""
        if not settings or not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env")

        # BUG FIX: Add timeout to prevent hanging requests
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            timeout=AIDecisionConfig.API_REQUEST_TIMEOUT,  # Add request timeout
        )

        self.site_url = settings.openrouter_site_url
        self.site_name = settings.openrouter_site_name

        logger.info(f"OpenRouter client initialized (timeout: {AIDecisionConfig.API_REQUEST_TIMEOUT}s)")

    def chat_completion(
        self,
        model: str,
        messages: list,
        temperature: float = AIDecisionConfig.TEMPERATURE,
        max_tokens: int = AIDecisionConfig.MAX_TOKENS,
        use_json_mode: bool = False,
        max_retries: int = 2,
    ) -> Optional[Dict]:
        """
        Get chat completion from model with retry logic

        Args:
            model: Model name (e.g., "deepseek/deepseek-chat-v3.1")
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            use_json_mode: Force JSON response format
            max_retries: Maximum number of retries on failure

        Returns:
            Dict with response data or None if failed
        """
        start_time = time.time()
        last_error = None

        # BUG FIX: Add retry logic for network failures
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    log_ai(f"Retry attempt {attempt}/{max_retries} for {model}...")
                    time.sleep(2 * attempt)  # Exponential backoff
                # Build request parameters
                request_params = {
                    "extra_headers": {
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name,
                    },
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # Add structured JSON schema mode if requested
                if use_json_mode:
                    # BUG FIX: Enhanced JSON schema with stricter validation
                    request_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "trading_decision",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "decision": {
                                        "type": "string",
                                        "description": "Trading decision: BUY, SELL, or HOLD",
                                        "enum": ["BUY", "SELL", "HOLD"]
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "description": (
                                            "Confidence level MUST be between 0.0 and 1.0 (decimal format). "
                                            "Examples: 0.75 for 75% confidence, 0.6 for 60% confidence. "
                                            "DO NOT use percentages (0-100) or ratings (1-10)."
                                        ),
                                        "minimum": 0.0,
                                        "maximum": 1.0
                                    },
                                    "reasoning": {
                                        "type": "string",
                                        "description": "Detailed explanation of the decision (50-500 characters)",
                                        "minLength": 50,
                                        "maxLength": 500
                                    }
                                },
                                "required": ["decision", "confidence", "reasoning"],
                                "additionalProperties": False
                            }
                        }
                    }

                response = self.client.chat.completions.create(**request_params)

                response_time = time.time() - start_time

                # Extract response
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason

                result = {
                    'model': model,
                    'content': content,
                    'finish_reason': finish_reason,
                    'response_time': response_time,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens,
                    } if response.usage else None
                }

                log_ai(f"AI response from {model} ({response_time:.2f}s)")

                return result

            except Exception as e:
                last_error = e
                # Log different error types appropriately
                if "timeout" in str(e).lower():
                    log_error(f"OpenRouter API timeout for {model} (attempt {attempt + 1}/{max_retries + 1}): {e}")
                elif "connection" in str(e).lower() or "network" in str(e).lower():
                    log_error(f"OpenRouter API connection error for {model} (attempt {attempt + 1}/{max_retries + 1}): {e}")
                else:
                    log_error(f"OpenRouter API error for {model} (attempt {attempt + 1}/{max_retries + 1}): {e}")

                # Don't retry on last attempt
                if attempt >= max_retries:
                    break

        # All retries failed
        log_error(f"OpenRouter API failed after {max_retries + 1} attempts for {model}. Last error: {last_error}")
        return None

    def get_decision(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> Optional[Dict]:
        """
        Get trading decision from AI model

        Args:
            model: Model name
            system_prompt: System instructions
            user_prompt: User query with market data

        Returns:
            Dict with decision data
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Use JSON mode for structured response
        response = self.chat_completion(model, messages, use_json_mode=True)

        if not response:
            return None

        # Parse AI response
        try:
            decision_data = self._parse_decision_response(response['content'])
            decision_data['model'] = model
            decision_data['response_time'] = response['response_time']
            decision_data['raw_response'] = response['content']

            log_ai(f"Parsed decision: {decision_data['decision']} (confidence: {decision_data['confidence']:.2f})")

            return decision_data

        except Exception as e:
            log_error(f"Failed to parse AI decision: {e}")
            log_error(f"Raw response: {response.get('content', 'N/A')[:500]}")
            return None

    def _parse_decision_response(self, content: str) -> Dict:
        """
        Parse AI decision response from JSON format

        Expected JSON format:
        {
          "decision": "BUY" | "SELL" | "HOLD",
          "confidence": 0.0-1.0,
          "reasoning": "explanation"
        }

        Args:
            content: AI response content (JSON string)

        Returns:
            Parsed decision dict

        Raises:
            ValueError: If JSON parsing fails or required fields are missing
        """
        # Default values
        decision = "HOLD"
        confidence = 0.5
        reasoning = "Failed to parse AI response"

        try:
            # Parse JSON response
            data = json.loads(content.strip())

            # Extract decision
            if 'decision' in data:
                decision_text = str(data['decision']).strip().upper()
                if decision_text in ["BUY", "SELL", "HOLD", "LONG", "SHORT"]:
                    decision = decision_text
                    # Convert LONG/SHORT to BUY/SELL
                    if decision == "LONG":
                        decision = "BUY"
                    elif decision == "SHORT":
                        decision = "SELL"
                else:
                    log_error(f"Invalid decision value: {decision_text}, defaulting to HOLD")
                    decision = "HOLD"

            # Extract confidence with improved normalization
            if 'confidence' in data:
                try:
                    conf_value = float(data['confidence'])

                    # BUG FIX: More robust confidence normalization
                    # Handle different scales that AI models might return:
                    # - 0-1 scale (preferred): use as-is
                    # - 0-100 scale (percentage): divide by 100
                    # - 1-10 scale (rating): divide by 10
                    # - Other ranges: clamp to 0-1 and warn

                    if 0.0 <= conf_value <= 1.0:
                        # Already in correct range (0-1)
                        confidence = conf_value
                    elif 1.0 < conf_value <= 10.0:
                        # Likely 1-10 scale - convert to 0-1
                        confidence = conf_value / 10.0
                        log_ai(f"Confidence {conf_value} detected as 1-10 scale, normalized to {confidence:.2f}")
                    elif 10.0 < conf_value <= 100.0:
                        # Likely 0-100 percentage scale - convert to 0-1
                        confidence = conf_value / 100.0
                        log_ai(f"Confidence {conf_value}% detected as percentage, normalized to {confidence:.2f}")
                    else:
                        # Out of expected ranges - clamp and warn
                        log_error(
                            f"Unexpected confidence value: {conf_value}. "
                            f"Expected 0-1, 1-10, or 0-100. Clamping to valid range."
                        )
                        confidence = min(max(conf_value / 100.0, 0.0), 1.0)

                    # Final safety clamp
                    confidence = min(max(confidence, 0.0), 1.0)

                except (ValueError, TypeError) as e:
                    log_error(f"Invalid confidence value '{data['confidence']}': {e}. Using default 0.5")
                    confidence = 0.5

            # Extract reasoning
            if 'reasoning' in data:
                reasoning = str(data['reasoning']).strip()
            else:
                reasoning = "No reasoning provided"

            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
            }

        except json.JSONDecodeError as e:
            log_error(f"JSON parsing failed: {e}")
            log_error(f"Content: {content[:500]}")

            # Fallback: try to parse as old text format for backwards compatibility
            return self._parse_legacy_text_format(content)

        except Exception as e:
            log_error(f"Unexpected error parsing decision: {e}")
            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
            }

    def _parse_legacy_text_format(self, content: str) -> Dict:
        """
        Fallback parser for legacy text format (DECISION:, CONFIDENCE:, REASONING:)

        Args:
            content: AI response content in text format

        Returns:
            Parsed decision dict
        """
        log_ai("Attempting to parse legacy text format as fallback...")

        lines = content.strip().split('\n')

        decision = "HOLD"
        confidence = 0.5
        reasoning = content

        # Parse structured response
        for line in lines:
            line = line.strip()

            if line.startswith("DECISION:"):
                decision_text = line.split(":", 1)[1].strip().upper()
                if decision_text in ["BUY", "SELL", "HOLD", "LONG", "SHORT"]:
                    decision = decision_text
                    # Convert LONG/SHORT to BUY/SELL
                    if decision == "LONG":
                        decision = "BUY"
                    elif decision == "SHORT":
                        decision = "SELL"

            elif line.startswith("CONFIDENCE:"):
                try:
                    conf_text = line.split(":", 1)[1].strip()
                    # Remove % if present
                    conf_text = conf_text.replace("%", "")
                    conf_value = float(conf_text)

                    # Normalize to 0-1 range
                    if conf_value > 1:
                        conf_value = conf_value / 100.0

                    confidence = min(max(conf_value, 0.0), 1.0)
                except ValueError:
                    pass

            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        return {
            'decision': decision,
            'confidence': confidence,
            'reasoning': reasoning,
        }


__all__ = ["OpenRouterClient"]
