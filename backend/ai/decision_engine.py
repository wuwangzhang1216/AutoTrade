"""
AI Decision Engine with dual model comparison
"""
import time
from typing import Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import logger, log_ai, log_error
from config import settings, AIDecisionConfig
from .openrouter_client import OpenRouterClient
from .prompt_templates import SYSTEM_PROMPT, create_market_analysis_prompt


class AIDecisionEngine:
    """
    AI-powered trading decision engine
    Uses two models in parallel and compares their decisions
    """

    def __init__(self):
        """Initialize AI decision engine"""
        self.client = OpenRouterClient()

        # Model configuration
        self.model_1 = settings.ai_model_primary  # DeepSeek
        self.model_2 = settings.ai_model_secondary  # Qwen

        logger.info(f"AI Decision Engine initialized")
        logger.info(f"Model 1: {self.model_1}")
        logger.info(f"Model 2: {self.model_2}")
        logger.info(f"Voting strategy: {AIDecisionConfig.VOTING_STRATEGY}")

    def get_single_model_decision(
        self,
        model: str,
        symbol: str,
        current_price: float,
        technical_summary: dict,
        fundamental_analysis: dict,
        market_sentiment: dict,
        # Enhanced context parameters (optional)
        current_time: Optional = None,
        account_context: Optional[Dict] = None,
        position_context: Optional[Dict] = None,
        historical_context: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        Get decision from a single AI model

        Args:
            model: Model name
            symbol: Trading pair
            current_price: Current price
            technical_summary: Technical analysis
            fundamental_analysis: Fundamental analysis
            market_sentiment: Market sentiment
            current_time: Current datetime (optional)
            account_context: Account status info (optional)
            position_context: Current position for this symbol (optional)
            historical_context: Last AI decision for this symbol (optional)

        Returns:
            Decision dict or None if failed
        """
        # Create prompt with enhanced context
        user_prompt = create_market_analysis_prompt(
            symbol=symbol,
            current_price=current_price,
            technical_summary=technical_summary,
            fundamental_analysis=fundamental_analysis,
            market_sentiment=market_sentiment,
            # Pass enhanced context
            current_time=current_time,
            account_context=account_context,
            position_context=position_context,
            historical_context=historical_context,
        )

        # Get decision from model
        decision = self.client.get_decision(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return decision

    def get_dual_model_decision(
        self,
        symbol: str,
        current_price: float,
        technical_summary: dict,
        fundamental_analysis: dict,
        market_sentiment: dict,
        # Enhanced context parameters (optional)
        current_time: Optional = None,
        account_context: Optional[Dict] = None,
        position_context: Optional[Dict] = None,
        historical_context: Optional[Dict] = None,
    ) -> Tuple[Optional[Dict], Optional[Dict], str]:
        """
        Get decisions from both models in parallel

        Args:
            symbol: Trading pair
            current_price: Current price
            technical_summary: Technical analysis
            fundamental_analysis: Fundamental analysis
            market_sentiment: Market sentiment
            current_time: Current datetime (optional)
            account_context: Account status info (optional)
            position_context: Current position for this symbol (optional)
            historical_context: Last AI decision for this symbol (optional)

        Returns:
            Tuple of (model_1_decision, model_2_decision, final_decision)
        """
        log_ai(f"Requesting AI decisions for {symbol} from both models...")

        model_1_decision = None
        model_2_decision = None

        # Execute both models in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            future_1 = executor.submit(
                self.get_single_model_decision,
                self.model_1,
                symbol,
                current_price,
                technical_summary,
                fundamental_analysis,
                market_sentiment,
                # Pass enhanced context
                current_time,
                account_context,
                position_context,
                historical_context,
            )

            future_2 = executor.submit(
                self.get_single_model_decision,
                self.model_2,
                symbol,
                current_price,
                technical_summary,
                fundamental_analysis,
                market_sentiment,
                # Pass enhanced context
                current_time,
                account_context,
                position_context,
                historical_context,
            )

            # BUG FIX: Wait for results with timeout to prevent hanging
            # Use configurable timeout for both requests to complete
            import concurrent.futures
            timeout_seconds = AIDecisionConfig.DECISION_TIMEOUT

            try:
                for future in as_completed([future_1, future_2], timeout=timeout_seconds):
                    try:
                        # Additional 5-second buffer for individual result retrieval
                        result = future.result(timeout=5)

                        if future == future_1:
                            model_1_decision = result
                            if result:
                                log_ai(f"Model 1 ({self.model_1}): {result['decision']} (confidence: {result['confidence']:.2f})")
                        else:
                            model_2_decision = result
                            if result:
                                log_ai(f"Model 2 ({self.model_2}): {result['decision']} (confidence: {result['confidence']:.2f})")

                    except concurrent.futures.TimeoutError:
                        # Individual future timed out
                        if future == future_1:
                            log_error(f"Model 1 ({self.model_1}) request timed out")
                        else:
                            log_error(f"Model 2 ({self.model_2}) request timed out")
                    except Exception as e:
                        log_error(f"Error getting AI decision: {e}")

            except concurrent.futures.TimeoutError:
                # Overall timeout - at least one model didn't respond
                log_error(f"AI decision requests timed out after {timeout_seconds} seconds")
                log_error(f"Individual API timeout is set to {AIDecisionConfig.API_REQUEST_TIMEOUT}s")
                log_error("Consider increasing DECISION_TIMEOUT or API_REQUEST_TIMEOUT in config if this persists")
                # Cancel any pending futures
                future_1.cancel()
                future_2.cancel()

        # Compare and determine final decision
        final_decision = self._compare_decisions(model_1_decision, model_2_decision)

        log_ai(f"Final decision: {final_decision}")

        return model_1_decision, model_2_decision, final_decision

    def _compare_decisions(
        self,
        decision_1: Optional[Dict],
        decision_2: Optional[Dict]
    ) -> str:
        """
        Compare two model decisions and determine final decision

        Args:
            decision_1: Model 1 decision
            decision_2: Model 2 decision

        Returns:
            Final decision (BUY/SELL/HOLD)
        """
        # If either model failed, use the other or default to HOLD
        if not decision_1 and not decision_2:
            logger.warning("Both models failed, defaulting to HOLD")
            return "HOLD"

        if not decision_1:
            logger.warning("Model 1 failed, using Model 2 decision")
            return decision_2['decision']

        if not decision_2:
            logger.warning("Model 2 failed, using Model 1 decision")
            return decision_1['decision']

        # Both models responded
        strategy = AIDecisionConfig.VOTING_STRATEGY

        if strategy == "majority":
            return self._majority_vote(decision_1, decision_2)

        elif strategy == "unanimous":
            return self._unanimous_vote(decision_1, decision_2)

        elif strategy == "weighted":
            return self._weighted_vote(decision_1, decision_2)

        else:
            logger.warning(f"Unknown voting strategy: {strategy}, using majority")
            return self._majority_vote(decision_1, decision_2)

    def _majority_vote(self, decision_1: Dict, decision_2: Dict) -> str:
        """
        Majority voting: If both agree, use that. Otherwise HOLD.

        Improved logic:
        - Check confidence quality even when models agree
        - Use confidence threshold of 0.2 (20%) for tiebreaking
        - More defensive when confidence is marginal

        Args:
            decision_1: Model 1 decision
            decision_2: Model 2 decision

        Returns:
            Final decision
        """
        min_confidence = AIDecisionConfig.MIN_CONFIDENCE
        conf_1 = decision_1['confidence']
        conf_2 = decision_2['confidence']
        avg_confidence = (conf_1 + conf_2) / 2

        if decision_1['decision'] == decision_2['decision']:
            # Both agree
            decision = decision_1['decision']

            # Quality check: even if both agree, verify confidence is sufficient
            if decision != "HOLD" and avg_confidence < min_confidence:
                logger.warning(
                    f"Majority vote: Models agree on {decision} but average confidence "
                    f"({avg_confidence:.2f}) below threshold ({min_confidence:.2f}). "
                    f"Downgrading to HOLD."
                )
                return "HOLD"

            logger.info(
                f"Majority vote: Both models agree on {decision} "
                f"(confidences: {conf_1:.2f}, {conf_2:.2f})"
            )
            return decision
        else:
            # Disagreement - check confidence
            # Confidence difference threshold for tiebreaking (20%)
            CONFIDENCE_DIFF_THRESHOLD = 0.2

            # If one model has significantly higher confidence, use that decision
            # BUT only if it meets minimum confidence threshold
            if conf_1 > conf_2 + CONFIDENCE_DIFF_THRESHOLD:
                winner_decision = decision_1['decision']
                winner_confidence = conf_1

                if winner_decision != "HOLD" and winner_confidence < min_confidence:
                    logger.info(
                        f"Majority vote: Model 1 has higher confidence ({conf_1:.2f} vs {conf_2:.2f}) "
                        f"but still below threshold ({min_confidence:.2f}). Defaulting to HOLD."
                    )
                    return "HOLD"

                logger.info(
                    f"Majority vote: Model 1 wins with higher confidence "
                    f"({conf_1:.2f} vs {conf_2:.2f}) -> {winner_decision}"
                )
                return winner_decision

            elif conf_2 > conf_1 + CONFIDENCE_DIFF_THRESHOLD:
                winner_decision = decision_2['decision']
                winner_confidence = conf_2

                if winner_decision != "HOLD" and winner_confidence < min_confidence:
                    logger.info(
                        f"Majority vote: Model 2 has higher confidence ({conf_2:.2f} vs {conf_1:.2f}) "
                        f"but still below threshold ({min_confidence:.2f}). Defaulting to HOLD."
                    )
                    return "HOLD"

                logger.info(
                    f"Majority vote: Model 2 wins with higher confidence "
                    f"({conf_2:.2f} vs {conf_1:.2f}) -> {winner_decision}"
                )
                return winner_decision

            else:
                # Similar confidence but different decisions - be conservative
                logger.info(
                    f"Majority vote: Models disagree ({decision_1['decision']} vs {decision_2['decision']}) "
                    f"with similar confidence ({conf_1:.2f} vs {conf_2:.2f}). Defaulting to HOLD."
                )
                return "HOLD"

    def _unanimous_vote(self, decision_1: Dict, decision_2: Dict) -> str:
        """
        Unanimous voting: Only trade if both agree

        Improved logic:
        - Check confidence quality even when models agree
        - Most conservative strategy - both must agree AND have good confidence

        Args:
            decision_1: Model 1 decision
            decision_2: Model 2 decision

        Returns:
            Final decision
        """
        if decision_1['decision'] == decision_2['decision']:
            decision = decision_1['decision']
            min_confidence = AIDecisionConfig.MIN_CONFIDENCE
            avg_confidence = (decision_1['confidence'] + decision_2['confidence']) / 2

            # Quality check: verify confidence is sufficient
            if decision != "HOLD" and avg_confidence < min_confidence:
                logger.warning(
                    f"Unanimous vote: Models agree on {decision} but average confidence "
                    f"({avg_confidence:.2f}) below threshold ({min_confidence:.2f}). "
                    f"Downgrading to HOLD."
                )
                return "HOLD"

            logger.info(
                f"Unanimous vote: Both models agree on {decision} "
                f"(confidences: {decision_1['confidence']:.2f}, {decision_2['confidence']:.2f})"
            )
            return decision
        else:
            logger.info(
                f"Unanimous vote: Models disagree ({decision_1['decision']} vs {decision_2['decision']}), "
                f"defaulting to HOLD"
            )
            return "HOLD"

    def _weighted_vote(self, decision_1: Dict, decision_2: Dict) -> str:
        """
        Weighted voting: Use model weights and confidence

        Improved logic:
        - Even when models agree, check if combined confidence is sufficient
        - Use weighted scores to determine final decision
        - More transparent decision-making process

        Args:
            decision_1: Model 1 decision
            decision_2: Model 2 decision

        Returns:
            Final decision
        """
        weights = AIDecisionConfig.MODEL_WEIGHTS

        weight_1 = weights.get(self.model_1, 0.5)
        weight_2 = weights.get(self.model_2, 0.5)

        # Calculate weighted confidence for each decision
        score_1 = decision_1['confidence'] * weight_1
        score_2 = decision_2['confidence'] * weight_2

        # Get the min confidence threshold for quality check
        min_confidence = AIDecisionConfig.MIN_CONFIDENCE

        # Calculate average confidence for quality assessment
        avg_confidence = (decision_1['confidence'] + decision_2['confidence']) / 2

        # If decisions agree
        if decision_1['decision'] == decision_2['decision']:
            decision = decision_1['decision']

            # Quality check: Even if both agree, check if confidence is sufficient
            # This prevents executing low-confidence unanimous decisions
            if decision != "HOLD" and avg_confidence < min_confidence:
                logger.warning(
                    f"Models agree on {decision} but average confidence ({avg_confidence:.2f}) "
                    f"below threshold ({min_confidence:.2f}). Downgrading to HOLD for safety."
                )
                return "HOLD"

            logger.info(
                f"Weighted vote: Both models agree on {decision} "
                f"(avg confidence: {avg_confidence:.2f}, scores: {score_1:.3f}, {score_2:.3f})"
            )
            return decision

        # Models disagree - use weighted scores to determine winner
        # But also check if the winning score meets minimum quality standards
        if score_1 > score_2:
            winner_decision = decision_1['decision']
            winner_score = score_1
            winner_confidence = decision_1['confidence']
            loser_decision = decision_2['decision']
            loser_score = score_2
        else:
            winner_decision = decision_2['decision']
            winner_score = score_2
            winner_confidence = decision_2['confidence']
            loser_decision = decision_1['decision']
            loser_score = score_1

        # Score difference threshold: if scores are too close, be conservative
        score_diff = abs(score_1 - score_2)
        SCORE_DIFF_THRESHOLD = 0.15  # Require at least 15% difference in weighted scores

        if score_diff < SCORE_DIFF_THRESHOLD:
            logger.info(
                f"Weighted vote: Models disagree ({decision_1['decision']} vs {decision_2['decision']}) "
                f"and scores too close ({score_1:.3f} vs {score_2:.3f}, diff={score_diff:.3f}). "
                f"Defaulting to HOLD for safety."
            )
            return "HOLD"

        # Even with clear winner, check confidence quality
        if winner_decision != "HOLD" and winner_confidence < min_confidence:
            logger.info(
                f"Weighted vote: {winner_decision} wins ({winner_score:.3f} vs {loser_score:.3f}) "
                f"but confidence ({winner_confidence:.2f}) below threshold ({min_confidence:.2f}). "
                f"Defaulting to HOLD."
            )
            return "HOLD"

        logger.info(
            f"Weighted vote: {winner_decision} wins over {loser_decision} "
            f"({winner_score:.3f} vs {loser_score:.3f}, confidence: {winner_confidence:.2f})"
        )
        return winner_decision

    def should_execute_decision(
        self,
        decision: str,
        model_1_decision: Optional[Dict],
        model_2_decision: Optional[Dict]
    ) -> bool:
        """
        Determine if decision should be executed based on confidence threshold

        Improved logic:
        - Handle single-model failure scenarios more gracefully
        - Use adjusted threshold when only one model is available
        - More detailed logging for transparency

        Args:
            decision: Final decision
            model_1_decision: Model 1 decision
            model_2_decision: Model 2 decision

        Returns:
            True if should execute
        """
        if decision == "HOLD":
            return False

        # Check if we have valid decisions
        if not model_1_decision and not model_2_decision:
            logger.warning("No valid AI decisions available, cannot execute")
            return False

        # Count available models
        available_models = 0
        confidences = []

        if model_1_decision:
            available_models += 1
            confidences.append(model_1_decision['confidence'])

        if model_2_decision:
            available_models += 1
            confidences.append(model_2_decision['confidence'])

        avg_confidence = sum(confidences) / len(confidences)

        # Determine appropriate confidence threshold
        min_confidence = AIDecisionConfig.MIN_CONFIDENCE

        # Single-model fallback logic
        if available_models == 1:
            # When only one model is available, use a slightly relaxed threshold
            # to avoid being overly conservative and missing opportunities
            # But still maintain a safety margin
            SINGLE_MODEL_THRESHOLD_REDUCTION = 0.05  # 5% reduction (e.g., 0.6 -> 0.55)
            adjusted_threshold = max(0.5, min_confidence - SINGLE_MODEL_THRESHOLD_REDUCTION)

            single_model_name = (
                f"Model 1 ({self.model_1})" if model_1_decision else f"Model 2 ({self.model_2})"
            )

            if avg_confidence >= min_confidence:
                # Meets the standard threshold - excellent
                logger.info(
                    f"Single model scenario ({single_model_name}): "
                    f"Confidence {avg_confidence:.2f} meets standard threshold {min_confidence:.2f}"
                )
                return True
            elif avg_confidence >= adjusted_threshold:
                # Meets the adjusted threshold for single-model scenario
                logger.info(
                    f"Single model scenario ({single_model_name}): "
                    f"Confidence {avg_confidence:.2f} meets adjusted threshold {adjusted_threshold:.2f} "
                    f"(standard: {min_confidence:.2f}). Proceeding with caution."
                )
                return True
            else:
                # Below even the adjusted threshold
                logger.warning(
                    f"Single model scenario ({single_model_name}): "
                    f"Confidence {avg_confidence:.2f} below adjusted threshold {adjusted_threshold:.2f}. "
                    f"Skipping execution for safety."
                )
                return False

        # Both models available - use standard threshold
        else:
            if avg_confidence >= min_confidence:
                logger.info(
                    f"Both models available: Average confidence {avg_confidence:.2f} "
                    f"meets threshold {min_confidence:.2f}"
                )
                return True
            else:
                logger.warning(
                    f"Both models available: Average confidence {avg_confidence:.2f} "
                    f"below threshold {min_confidence:.2f}. Skipping execution."
                )
                return False


__all__ = ["AIDecisionEngine"]
