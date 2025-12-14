"""
AutoTrade AI - Autonomous Cryptocurrency Trading System
Main entry point
"""
import sys
import time
import signal
from datetime import datetime
from typing import Dict, Optional

from rich.panel import Panel
from rich.table import Table

# Configuration
from config import (
    settings,
    TradingPairsConfig,
    DirectoryConfig,
)

# Core components
from core import TradingEngine
from data import MarketDataCollector
from analysis import TechnicalAnalyzer, FundamentalAnalyzer
from ai import AIDecisionEngine
from database import get_db_manager

# Utilities
from utils import (
    logger,
    log_info,
    log_success,
    log_error,
    log_trade,
    log_ai,
    log_separator,
    console,
    format_currency,
    format_percentage,
)


class AutoTradeSystem:
    """
    Main AutoTrade AI system
    """

    def __init__(self):
        """Initialize AutoTrade system"""
        log_separator()
        console.print(Panel.fit(
            "[bold cyan]AutoTrade AI - Autonomous Trading System[/bold cyan]\n"
            "[dim]Powered by DeepSeek & Qwen via OpenRouter[/dim]",
            border_style="cyan"
        ))
        log_separator()

        # Validate configuration
        if not settings:
            log_error("Configuration not loaded. Please create .env file from .env.example")
            sys.exit(1)

        # Create directories
        DirectoryConfig.create_directories()

        # Initialize components
        log_info("Initializing system components...")

        self.trading_engine = TradingEngine(
            initial_capital=settings.initial_capital,
            leverage=settings.leverage,
            commission_rate=settings.commission_rate,
            max_positions=TradingPairsConfig.MAX_POSITIONS
        )

        self.market_data = MarketDataCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.ai_engine = AIDecisionEngine()
        self.db = get_db_manager()

        # Trading state
        self.trading_pairs = TradingPairsConfig.DEFAULT_PAIRS
        self.running = False

        log_success("System initialized successfully!")
        log_separator()

    def test_connections(self) -> bool:
        """Test all external connections"""
        log_info("Testing connections...")

        # Test exchange connection
        if not self.market_data.test_connection():
            log_error("Exchange connection failed")
            return False

        log_success("All connections successful!")
        return True

    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Perform complete analysis for a symbol

        Args:
            symbol: Trading pair

        Returns:
            Analysis dict or None if failed
        """
        log_info(f"Analyzing {symbol}...")

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

            log_success(f"Analysis complete for {symbol}")

            return analysis

        except KeyError as e:
            # BUG FIX: Data format error - likely a bug in code
            log_error(f"Data format error analyzing {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.db.log_system_event(
                "ERROR",
                "ANALYSIS",
                f"KeyError during analysis: {e}",
                {"symbol": symbol, "error": str(e)}
            )
            return None
        except (ConnectionError, TimeoutError) as e:
            # BUG FIX: Network errors - recoverable
            log_error(f"Network error analyzing {symbol}: {e}")
            return None
        except Exception as e:
            # BUG FIX: Unknown errors - log with full traceback
            log_error(f"Unexpected error analyzing {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.db.log_system_event(
                "ERROR",
                "ANALYSIS",
                f"Unexpected error: {e}",
                {"symbol": symbol, "error": str(e), "type": type(e).__name__}
            )
            return None

    def make_trading_decision(self, symbol: str, analysis: Dict) -> bool:
        """
        Make and execute trading decision using AI

        Args:
            symbol: Trading pair
            analysis: Analysis data

        Returns:
            True if trade executed
        """
        log_ai(f"Requesting AI trading decision for {symbol}...")

        try:
            current_price = analysis['current_price']
            technical_summary = analysis['technical_summary']
            fundamental_analysis = analysis['fundamental_analysis']
            market_sentiment = analysis['market_sentiment']

            # ═══════════════════════════════════════════════════════════════════
            # ENHANCED: Collect context data for AI decision
            # ═══════════════════════════════════════════════════════════════════
            from datetime import datetime, timezone

            # 1. Current time (UTC)
            current_time = datetime.now(timezone.utc)

            # 2. Account context - get current account status
            try:
                current_prices = self.market_data.get_multiple_prices(self.trading_pairs)
                account_summary = self.trading_engine.get_account_summary(current_prices)

                account_context = {
                    'total_equity': account_summary['total_equity'],
                    'capital': account_summary['capital'],
                    'total_pnl': account_summary['total_pnl'],
                    'total_pnl_percent': account_summary['total_pnl_percent'],
                    'open_positions': account_summary['open_positions'],
                    'max_positions': self.trading_engine.max_positions,
                    'performance': {
                        'total_trades': account_summary['total_trades'],
                        'winning_trades': account_summary['winning_trades'],
                        'losing_trades': account_summary['losing_trades'],
                        'win_rate': account_summary['win_rate'],
                    }
                }
            except Exception as e:
                log_error(f"Failed to collect account context: {e}")
                account_context = None

            # 3. Position context - check if we have an open position for this symbol
            position_context = None
            if symbol in self.trading_engine.positions:
                try:
                    pos = self.trading_engine.positions[symbol]
                    unrealized_pnl = pos.update_unrealized_pnl(current_price)
                    pnl_percent = (unrealized_pnl / pos.margin) * 100 if pos.margin > 0 else 0
                    duration_minutes = int((datetime.now() - pos.open_time).total_seconds() / 60)

                    position_context = {
                        'side': pos.side.value,
                        'entry_price': pos.entry_price,
                        'amount': pos.amount,
                        'unrealized_pnl': unrealized_pnl,
                        'pnl_percent': pnl_percent,
                        'duration_minutes': duration_minutes,
                        'liquidation_price': pos.liquidation_price,
                        'margin': pos.margin,
                    }
                except Exception as e:
                    log_error(f"Failed to collect position context: {e}")
                    position_context = None

            # 4. Historical context - get last AI decision for this symbol
            historical_context = None
            try:
                recent_decisions = self.db.get_recent_ai_decisions(limit=1, symbol=symbol)
                if recent_decisions:
                    last = recent_decisions[0]
                    time_diff = datetime.now() - last.timestamp
                    minutes_ago = int(time_diff.total_seconds() / 60)

                    # Format time ago string
                    if minutes_ago < 60:
                        time_ago_str = f"{minutes_ago} minutes"
                    elif minutes_ago < 1440:  # Less than 24 hours
                        time_ago_str = f"{minutes_ago // 60} hours"
                    else:
                        time_ago_str = f"{minutes_ago // 1440} days"

                    historical_context = {
                        'decision': last.final_decision,
                        'price': last.market_data.get('price', 0) if last.market_data else 0,
                        'executed': last.executed,
                        'time_ago': time_ago_str,
                        'model_1_confidence': last.model_1_confidence,
                        'model_2_confidence': last.model_2_confidence,
                    }
            except Exception as e:
                log_error(f"Failed to collect historical context: {e}")
                historical_context = None

            # Get dual AI decision with enhanced context
            model_1_decision, model_2_decision, final_decision = self.ai_engine.get_dual_model_decision(
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

            # BUG FIX: Log AI decisions to database with proper error handling
            # Prevent crash if logging fails
            try:
                from config import AIDecisionConfig
                ai_decision = self.db.log_ai_decision(
                    symbol=symbol,
                    model_1_data=model_1_decision or {},
                    model_2_data=model_2_decision or {},
                    final_decision=final_decision,
                    decision_method=AIDecisionConfig.VOTING_STRATEGY,  # BUG FIX: Use voting strategy, not model name
                    technical_data=technical_summary,
                    fundamental_data=fundamental_analysis,
                    market_data={'price': current_price},
                )
            except Exception as e:
                log_error(f"Failed to log AI decision to database: {e}")
                # Continue execution even if logging fails
                ai_decision = None

            # Check if should execute
            should_execute = self.ai_engine.should_execute_decision(
                final_decision,
                model_1_decision,
                model_2_decision
            )

            if not should_execute:
                log_info(f"Decision {final_decision} not executed (confidence too low or HOLD)")
                # BUG FIX: Only update database if ai_decision was successfully created
                if ai_decision:
                    try:
                        self.db.update_ai_decision_execution(
                            decision_id=ai_decision.id,
                            executed=False,
                            execution_reason="Confidence below threshold or HOLD decision"
                        )
                    except Exception as e:
                        log_error(f"Failed to update AI decision execution status: {e}")
                return False

            # Execute decision
            executed = self.execute_trade(symbol, final_decision, current_price, model_1_decision, model_2_decision)

            # BUG FIX: Update AI decision execution status with error handling
            if ai_decision:
                try:
                    if executed:
                        self.db.update_ai_decision_execution(
                            decision_id=ai_decision.id,
                            executed=True,
                            execution_reason="Trade executed successfully"
                        )
                        log_success(f"Trade executed successfully for {symbol}")
                    else:
                        self.db.update_ai_decision_execution(
                            decision_id=ai_decision.id,
                            executed=False,
                            execution_reason="Trade execution failed"
                        )
                except Exception as e:
                    log_error(f"Failed to update AI decision execution status: {e}")
            else:
                # AI decision logging failed earlier, but trade was still attempted
                if executed:
                    log_success(f"Trade executed successfully for {symbol} (AI decision not logged)")

            return executed

        except Exception as e:
            log_error(f"Trading decision failed for {symbol}: {e}")
            return False

    def execute_trade(
        self,
        symbol: str,
        decision: str,
        current_price: float,
        model_1_decision: Optional[Dict],
        model_2_decision: Optional[Dict]
    ) -> bool:
        """
        Execute trading decision

        Args:
            symbol: Trading pair
            decision: BUY/SELL/HOLD
            current_price: Current price
            model_1_decision: Model 1 decision data
            model_2_decision: Model 2 decision data

        Returns:
            True if executed
        """
        # Calculate position size
        # BUG FIX: Leverage should MULTIPLY position value, not divide amount
        # Formula: margin = capital * position_size_pct
        #          position_value = margin * leverage (leverage amplifies position)
        #          amount = position_value / current_price
        position_size_pct = TradingPairsConfig.POSITION_SIZE_PERCENT / 100

        # BUG FIX: When position size is 100%, we need to reserve capital for fees
        # Otherwise margin + fee > capital and trade will always fail
        # Fixed fee is $2.99 per trade
        FIXED_FEE = 2.99
        available_for_margin = max(0, self.trading_engine.capital - FIXED_FEE)

        margin = available_for_margin * position_size_pct
        position_value = margin * self.trading_engine.leverage  # Apply leverage correctly
        amount = position_value / current_price

        # Log for debugging
        log_info(f"Position calculation: margin={format_currency(margin)}, "
                f"leverage={self.trading_engine.leverage}x, "
                f"position_value={format_currency(position_value)}, "
                f"amount={amount:.6f}")

        reasoning = ""
        if model_1_decision:
            reasoning += f"Model 1: {model_1_decision.get('reasoning', '')[:200]}\n"
        if model_2_decision:
            reasoning += f"Model 2: {model_2_decision.get('reasoning', '')[:200]}"

        if decision == "BUY":
            # BUG FIX: BUY should close SHORT positions or open LONG
            if symbol in self.trading_engine.positions:
                position = self.trading_engine.positions[symbol]

                if position.side.value == "SHORT":
                    # Close SHORT position (reverse trade)
                    # BUG FIX: close_position now returns (success, pnl) tuple
                    success, pnl = self.trading_engine.close_position(
                        symbol=symbol,
                        price=current_price,
                        reason=reasoning
                    )

                    if success:
                        # BUG FIX: Pass PnL to log_trade so it gets saved to database
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
                        log_success(f"BUY executed (closed SHORT): {symbol} @ {current_price}")

                    return success
                else:
                    # Already have LONG position
                    log_info(f"Already have LONG position in {symbol}, skipping BUY")
                    return False
            else:
                # Open new LONG position
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

                return success

        elif decision == "SELL":
            # BUG FIX: SELL should close LONG positions or open SHORT
            if symbol in self.trading_engine.positions:
                position = self.trading_engine.positions[symbol]

                if position.side.value == "LONG":
                    # Close LONG position (reverse trade)
                    # BUG FIX: close_position now returns (success, pnl) tuple
                    success, pnl = self.trading_engine.close_position(
                        symbol=symbol,
                        price=current_price,
                        reason=reasoning
                    )

                    if success:
                        # BUG FIX: Pass PnL to log_trade so it gets saved to database
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
                        log_success(f"SELL executed (closed LONG): {symbol} @ {current_price}")

                    return success
                else:
                    # Already have SHORT position
                    log_info(f"Already have SHORT position in {symbol}, skipping SELL")
                    return False
            else:
                # Open new SHORT position
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

                return success

        return False

    def trading_loop(self):
        """Main trading loop"""
        log_info("Starting trading loop...")
        log_info(f"Monitoring {len(self.trading_pairs)} pairs: {', '.join(self.trading_pairs)}")
        log_info(f"Trading interval: {settings.trading_interval_minutes} minutes")
        log_separator()

        iteration = 0

        while self.running:
            try:
                iteration += 1
                log_separator()
                log_info(f"Trading Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                log_separator()

                # Get current prices for all pairs
                current_prices = self.market_data.get_multiple_prices(self.trading_pairs)

                # Check for liquidations
                liquidated = self.trading_engine.check_liquidations(current_prices)
                if liquidated:
                    log_error(f"Liquidated positions: {', '.join(liquidated)}")

                # Show account status BEFORE trading
                self.trading_engine.print_account_summary(current_prices)

                # Analyze each trading pair
                for symbol in self.trading_pairs:
                    log_separator()
                    log_info(f"Processing {symbol}...")

                    # BUG FIX: Get fresh price for each symbol to avoid stale data
                    # This prevents race conditions where prices change during the loop
                    current_price = self.market_data.get_price(symbol)
                    if not current_price:
                        log_error(f"Failed to get current price for {symbol}, skipping")
                        continue

                    # BUG FIX: Check liquidation risk for this specific symbol before trading
                    # Price may have changed significantly since the batch check
                    if symbol in self.trading_engine.positions:
                        pos = self.trading_engine.positions[symbol]
                        if pos.is_liquidated(current_price):
                            log_error(f"Position {symbol} at liquidation risk, closing immediately")
                            # BUG FIX: close_position now returns (success, pnl) tuple - must unpack it
                            success, pnl = self.trading_engine.close_position(symbol, current_price, "Pre-trade liquidation check")

                            # Log the liquidation to database if successful
                            if success and pnl is not None:
                                try:
                                    self.db.log_trade(
                                        symbol=symbol,
                                        order_type=f"CLOSE_{pos.side.value}",
                                        amount=pos.amount,
                                        price=current_price,
                                        fee=self.trading_engine.calculate_fee(current_price, pos.amount),
                                        pnl=pnl,
                                        margin=pos.margin,
                                        leverage=pos.leverage,
                                        reason="Pre-trade liquidation check"
                                    )
                                    logger.info(f"✓ Liquidation trade logged to database: PnL = {pnl:.2f}")
                                except Exception as e:
                                    log_error(f"Failed to log liquidation trade: {e}")
                            elif not success:
                                log_error(f"Failed to close position {symbol} during liquidation check")

                            continue

                    # Perform analysis with fresh price
                    analysis = self.analyze_symbol(symbol)

                    if analysis:
                        # Make trading decision
                        self.make_trading_decision(symbol, analysis)

                    # Small delay between symbols
                    time.sleep(2)

                # BUG FIX: Save account snapshot AFTER all trades are executed
                # This ensures positions data is correctly saved to the database
                try:
                    # Get current prices
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
                log_success(f"Iteration #{iteration} complete")
                log_info(f"Next iteration in {settings.trading_interval_minutes} minutes...")
                log_separator()

                # Wait for next iteration
                time.sleep(settings.trading_interval_minutes * 60)

            except KeyboardInterrupt:
                log_info("Keyboard interrupt received")
                break
            except Exception as e:
                log_error(f"Error in trading loop: {e}")
                self.db.log_system_event("ERROR", "TRADING", f"Trading loop error: {e}")
                time.sleep(60)

    def run(self):
        """Start the trading system"""
        # Test connections
        if not self.test_connections():
            log_error("Connection tests failed, exiting")
            return

        # Set running flag
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())

        # Start trading loop
        try:
            self.trading_loop()
        finally:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        log_info("Shutting down...")
        self.running = False

        # Show final account summary
        current_prices = self.market_data.get_multiple_prices(self.trading_pairs)
        self.trading_engine.print_account_summary(current_prices)

        # Show performance stats
        stats = self.db.get_performance_stats()
        if stats:
            log_separator()
            log_info("PERFORMANCE SUMMARY")
            log_separator()
            log_info(f"Total Return: {format_currency(stats['total_return'])} ({format_percentage(stats['total_return_pct'])})")
            log_info(f"Total Trades: {stats['total_trades']}")
            log_info(f"Win Rate: {format_percentage(stats['win_rate'])}")
            log_info(f"Profit Factor: {stats['profit_factor']:.2f}")
            log_separator()

        log_success("AutoTrade AI system stopped")


def main():
    """Main entry point"""
    try:
        system = AutoTradeSystem()
        system.run()
    except Exception as e:
        log_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
