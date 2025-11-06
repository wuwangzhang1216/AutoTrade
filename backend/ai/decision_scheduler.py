"""
AI Decision Scheduler - Runs AI decision-making at 1-minute intervals
Separate from the main trading loop for frequent AI analysis
"""
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict
from threading import Thread

from utils.logger import logger, log_info, log_error, log_ai, log_separator, log_success, log_trade
from config import TradingPairsConfig, settings
from data import MarketDataCollector
from analysis import TechnicalAnalyzer, FundamentalAnalyzer
from database import get_db_manager
from core import TradingEngine
from .decision_engine import AIDecisionEngine


class AIDecisionScheduler:
    """
    Scheduler that runs AI decision-making every minute
    Independent of trading execution
    """

    def __init__(self, broadcast_callback=None, enable_trading=False, interval_minutes=5):
        """
        Initialize AI decision scheduler

        Args:
            broadcast_callback: Optional async callback to broadcast decisions via WebSocket
            enable_trading: If True, execute trades based on AI decisions
            interval_minutes: Decision cycle interval in minutes (default: 5 minutes)
        """
        self.ai_engine = AIDecisionEngine()
        self.market_data = MarketDataCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.db = get_db_manager()

        # Initialize trading engine if trading is enabled
        self.enable_trading = enable_trading
        if enable_trading:
            self.trading_engine = TradingEngine(
                initial_capital=settings.initial_capital,
                leverage=settings.leverage,
                commission_rate=settings.commission_rate,
                max_positions=TradingPairsConfig.MAX_POSITIONS
            )
            log_info("Trading engine initialized - AI will execute trades")
        else:
            self.trading_engine = None
            log_info("Trading disabled - AI will only analyze and log decisions")

        self.trading_pairs = TradingPairsConfig.DEFAULT_PAIRS
        self.running = False
        self.thread: Optional[Thread] = None
        self.broadcast_callback = broadcast_callback
        self.interval_minutes = interval_minutes

        log_info(f"AI Decision Scheduler initialized - {interval_minutes} minute interval")

    def analyze_symbol(self, symbol: str) -> Optional[dict]:
        """
        Perform complete analysis for a symbol

        Args:
            symbol: Trading pair

        Returns:
            Analysis dict or None if failed
        """
        try:
            # Get current price
            current_price = self.market_data.get_price(symbol)
            if not current_price:
                log_error(f"Failed to get price for {symbol}")
                return None

            # Get OHLCV data
            timeframe = TradingPairsConfig.PRIMARY_TIMEFRAME
            df = self.market_data.get_ohlcv(symbol, timeframe=timeframe, limit=200)

            if df is None or df.empty:
                log_error(f"Failed to get OHLCV data for {symbol}")
                return None

            # Calculate technical indicators
            df = self.technical_analyzer.calculate_all_indicators(df)

            # Get technical summary
            technical_summary = self.technical_analyzer.get_trading_summary(df, symbol)

            # Get fundamental analysis
            fundamental_analysis = self.fundamental_analyzer.get_comprehensive_analysis(symbol)

            # Get market sentiment
            market_sentiment = self.fundamental_analyzer.get_market_sentiment()

            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'technical_summary': technical_summary,
                'fundamental_analysis': fundamental_analysis,
                'market_sentiment': market_sentiment,
            }

            return analysis

        except Exception as e:
            log_error(f"Error analyzing {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def make_ai_decision(self, symbol: str, analysis: dict) -> Optional[dict]:
        """
        Make AI trading decision (analysis only, no execution)

        Args:
            symbol: Trading pair
            analysis: Analysis data

        Returns:
            Decision data dict or None if failed
        """
        log_ai(f"Requesting AI decision for {symbol}...")

        try:
            current_price = analysis['current_price']
            technical_summary = analysis['technical_summary']
            fundamental_analysis = analysis['fundamental_analysis']
            market_sentiment = analysis['market_sentiment']

            # Get dual AI decision
            model_1_decision, model_2_decision, final_decision = self.ai_engine.get_dual_model_decision(
                symbol=symbol,
                current_price=current_price,
                technical_summary=technical_summary,
                fundamental_analysis=fundamental_analysis,
                market_sentiment=market_sentiment,
            )

            # Log AI decision to database
            try:
                from config import AIDecisionConfig
                ai_decision = self.db.log_ai_decision(
                    symbol=symbol,
                    model_1_data=model_1_decision or {},
                    model_2_data=model_2_decision or {},
                    final_decision=final_decision,
                    decision_method=AIDecisionConfig.VOTING_STRATEGY,
                    technical_data=technical_summary,
                    fundamental_data=fundamental_analysis,
                    market_data={'price': current_price},
                )

                # Check if should execute the decision
                executed = False
                if self.enable_trading:
                    should_execute = self.ai_engine.should_execute_decision(
                        final_decision,
                        model_1_decision,
                        model_2_decision
                    )

                    if should_execute:
                        executed = self.execute_trade(symbol, final_decision, current_price, model_1_decision, model_2_decision, ai_decision.id)
                    else:
                        log_info(f"Decision {final_decision} not executed (confidence too low or HOLD)")

                # Prepare decision data for broadcast
                decision_data = {
                    'id': ai_decision.id,
                    'timestamp': ai_decision.timestamp.isoformat(),
                    'symbol': symbol,
                    'model_1_decision': model_1_decision.get('decision', 'N/A') if model_1_decision else 'N/A',
                    'model_1_confidence': model_1_decision.get('confidence', 0) if model_1_decision else 0,
                    'model_1_reasoning': model_1_decision.get('reasoning', '') if model_1_decision else '',
                    'model_2_decision': model_2_decision.get('decision', 'N/A') if model_2_decision else 'N/A',
                    'model_2_confidence': model_2_decision.get('confidence', 0) if model_2_decision else 0,
                    'model_2_reasoning': model_2_decision.get('reasoning', '') if model_2_decision else '',
                    'final_decision': final_decision,
                    'executed': executed,
                    'current_price': current_price,
                }

                log_ai(f"AI Decision for {symbol}: {final_decision} (executed: {executed})")

                return decision_data

            except Exception as e:
                log_error(f"Failed to log AI decision: {e}")
                return None

        except Exception as e:
            log_error(f"AI decision failed for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def execute_trade(
        self,
        symbol: str,
        decision: str,
        current_price: float,
        model_1_decision: Optional[Dict],
        model_2_decision: Optional[Dict],
        ai_decision_id: int
    ) -> bool:
        """
        Execute trading decision

        Args:
            symbol: Trading pair
            decision: BUY/SELL/HOLD
            current_price: Current price
            model_1_decision: Model 1 decision data
            model_2_decision: Model 2 decision data
            ai_decision_id: AI decision database ID

        Returns:
            True if executed
        """
        if not self.trading_engine:
            log_error("Trading engine not initialized")
            return False

        # Calculate position size
        position_size_pct = TradingPairsConfig.POSITION_SIZE_PERCENT / 100
        margin = self.trading_engine.capital * position_size_pct
        position_value = margin * self.trading_engine.leverage
        amount = position_value / current_price

        # Build reasoning from both models
        reasoning = f"AI Decision #{ai_decision_id}\n"
        if model_1_decision:
            reasoning += f"Model 1: {model_1_decision.get('reasoning', '')[:200]}\n"
        if model_2_decision:
            reasoning += f"Model 2: {model_2_decision.get('reasoning', '')[:200]}"

        try:
            if decision == "BUY":
                # BUY Decision:
                # 1. If has SHORT position -> Close it
                # 2. If has LONG position -> Stack (add to it)
                # 3. If no position -> Open new LONG

                if symbol in self.trading_engine.positions:
                    position = self.trading_engine.positions[symbol]

                    if position.side.value == "SHORT":
                        # Close SHORT position (reverse trade)
                        success, pnl = self.trading_engine.close_position(
                            symbol=symbol,
                            price=current_price,
                            reason=reasoning
                        )

                        if success:
                            self.db.log_trade(
                                symbol=symbol,
                                order_type="CLOSE_SHORT",
                                side="SHORT",
                                amount=position.amount,
                                price=current_price,
                                fee=self.trading_engine.calculate_fee(current_price, position.amount),
                                pnl=pnl,
                                reason=reasoning
                            )
                            log_trade(f"BUY executed (closed SHORT): {symbol} @ {current_price}")

                            self.db.update_ai_decision_execution(
                                decision_id=ai_decision_id,
                                executed=True,
                                execution_reason="BUY order executed (closed short position)"
                            )

                        return success

                # Open new LONG or stack existing LONG (open_long handles both)
                success = self.trading_engine.open_long(
                    symbol=symbol,
                    amount=amount,
                    price=current_price,
                    reason=reasoning
                )

                if success:
                    self.db.log_trade(
                        symbol=symbol,
                        order_type="OPEN_LONG",
                        side="LONG",
                        amount=amount,
                        price=current_price,
                        fee=self.trading_engine.calculate_fee(current_price, amount),
                        margin=self.trading_engine.get_position_size(current_price, amount),
                        leverage=self.trading_engine.leverage,
                        reason=reasoning
                    )

                    action = "stacked to" if symbol in self.trading_engine.positions else "opened"
                    log_trade(f"BUY executed ({action} LONG): {symbol} @ {current_price} (amount: {amount:.6f})")

                    self.db.update_ai_decision_execution(
                        decision_id=ai_decision_id,
                        executed=True,
                        execution_reason=f"BUY order executed ({action} long position)"
                    )

                return success

            elif decision == "SELL":
                # SELL Decision:
                # 1. If has LONG position -> Close it
                # 2. If has SHORT position -> Stack (add to it)
                # 3. If no position -> Open new SHORT

                if symbol in self.trading_engine.positions:
                    position = self.trading_engine.positions[symbol]

                    if position.side.value == "LONG":
                        # Close LONG position (reverse trade)
                        success, pnl = self.trading_engine.close_position(
                            symbol=symbol,
                            price=current_price,
                            reason=reasoning
                        )

                        if success:
                            self.db.log_trade(
                                symbol=symbol,
                                order_type="CLOSE_LONG",
                                side="LONG",
                                amount=position.amount,
                                price=current_price,
                                fee=self.trading_engine.calculate_fee(current_price, position.amount),
                                pnl=pnl,
                                reason=reasoning
                            )
                            log_trade(f"SELL executed (closed LONG): {symbol} @ {current_price}")

                            self.db.update_ai_decision_execution(
                                decision_id=ai_decision_id,
                                executed=True,
                                execution_reason="SELL order executed (closed long position)"
                            )

                        return success

                # Open new SHORT or stack existing SHORT (open_short handles both)
                success = self.trading_engine.open_short(
                    symbol=symbol,
                    amount=amount,
                    price=current_price,
                    reason=reasoning
                )

                if success:
                    self.db.log_trade(
                        symbol=symbol,
                        order_type="OPEN_SHORT",
                        side="SHORT",
                        amount=amount,
                        price=current_price,
                        fee=self.trading_engine.calculate_fee(current_price, amount),
                        margin=self.trading_engine.get_position_size(current_price, amount),
                        leverage=self.trading_engine.leverage,
                        reason=reasoning
                    )

                    action = "stacked to" if symbol in self.trading_engine.positions else "opened"
                    log_trade(f"SELL executed ({action} SHORT): {symbol} @ {current_price} (amount: {amount:.6f})")

                    self.db.update_ai_decision_execution(
                        decision_id=ai_decision_id,
                        executed=True,
                        execution_reason=f"SELL order executed ({action} short position)"
                    )

                return success

            return False

        except Exception as e:
            log_error(f"Trade execution failed for {symbol}: {e}")
            return False

    def run_decision_cycle(self):
        """Run one cycle of AI decisions for all trading pairs"""
        log_separator()
        log_info(f"AI Decision Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_separator()

        # Show account status if trading is enabled
        if self.enable_trading:
            current_prices = self.market_data.get_multiple_prices(self.trading_pairs)

            # Check for liquidations
            liquidated = self.trading_engine.check_liquidations(current_prices)
            if liquidated:
                log_error(f"Liquidated positions: {', '.join(liquidated)}")

            # Show account summary BEFORE trading
            self.trading_engine.print_account_summary(current_prices)

        decisions = []

        for symbol in self.trading_pairs:
            try:
                # Analyze symbol
                analysis = self.analyze_symbol(symbol)

                if analysis:
                    # Get AI decision
                    decision = self.make_ai_decision(symbol, analysis)

                    if decision:
                        decisions.append(decision)

                # Small delay between symbols
                time.sleep(1)

            except Exception as e:
                log_error(f"Error in decision cycle for {symbol}: {e}")

        # Broadcast all decisions via WebSocket
        if decisions and self.broadcast_callback:
            try:
                # Create event loop for async broadcast
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                for decision in decisions:
                    loop.run_until_complete(
                        self.broadcast_callback({
                            'type': 'ai_decision',
                            'data': decision
                        })
                    )

                loop.close()
                log_info(f"Broadcasted {len(decisions)} AI decisions via WebSocket")
            except Exception as e:
                log_error(f"Failed to broadcast decisions: {e}")

        # BUG FIX: Save account snapshot AFTER all trades are executed
        # This ensures positions data is correctly saved to the database
        if self.enable_trading:
            try:
                # Get current prices (filter out invalid pairs)
                current_prices = self.market_data.get_multiple_prices(self.trading_pairs)

                # Get account summary
                summary = self.trading_engine.get_account_summary(current_prices)

                # Save snapshot
                snapshot = self.db.save_account_snapshot({
                    'capital': summary['capital'],
                    'total_margin': summary['total_margin'],
                    'unrealized_pnl': summary['total_unrealized_pnl'],
                    'total_equity': summary['total_equity'],
                    'open_positions': summary['open_positions'],
                    'total_trades': summary['total_trades'],
                    'winning_trades': summary['winning_trades'],
                    'losing_trades': summary['losing_trades'],
                    'total_fees': summary['total_fees'],
                    'positions': {
                        symbol: {
                            'side': pos.side.value,
                            'amount': pos.amount,
                            'entry_price': pos.entry_price,
                            'unrealized_pnl': pos.unrealized_pnl,
                            'margin': pos.margin,
                            'leverage': pos.leverage
                        }
                        for symbol, pos in self.trading_engine.positions.items()
                    }
                })

                log_info(f"Account snapshot saved: {summary['open_positions']} positions, equity=${summary['total_equity']:.2f}")

            except Exception as e:
                log_error(f"Failed to save account snapshot: {e}")
                import traceback
                log_error(traceback.format_exc())

        log_separator()

    def scheduler_loop(self):
        """Main scheduler loop - runs at configured interval"""
        interval_seconds = self.interval_minutes * 60
        log_info(f"AI Decision Scheduler started - running every {self.interval_minutes} minutes")

        iteration = 0

        while self.running:
            try:
                iteration += 1

                # Run decision cycle
                self.run_decision_cycle()

                # Wait for next cycle
                log_info(f"AI Decision cycle #{iteration} complete. Next cycle in {interval_seconds} seconds...")
                time.sleep(interval_seconds)

            except Exception as e:
                log_error(f"Error in scheduler loop: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(interval_seconds)

    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            log_info("AI Decision Scheduler already running")
            return

        self.running = True
        self.thread = Thread(target=self.scheduler_loop, daemon=True)
        self.thread.start()
        log_info("AI Decision Scheduler thread started")

    def stop(self):
        """Stop the scheduler"""
        log_info("Stopping AI Decision Scheduler...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=5)

        log_info("AI Decision Scheduler stopped")


__all__ = ["AIDecisionScheduler"]
