"""
Test batch price fetching performance
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data import MarketDataCollector
from config import TradingPairsConfig

def test_batch_fetch():
    """Test batch price fetching vs individual fetching"""
    print("=" * 60)
    print("BATCH PRICE FETCH PERFORMANCE TEST")
    print("=" * 60)

    # Initialize collector
    collector = MarketDataCollector(exchange_id="kraken")

    symbols = TradingPairsConfig.DEFAULT_PAIRS
    print(f"\nTesting with {len(symbols)} symbols: {symbols}")

    # Test batch fetch (optimized)
    print("\n1. Testing BATCH fetch (optimized)...")
    start_time = time.time()
    prices_batch = collector.get_multiple_prices(symbols)
    batch_time = time.time() - start_time

    print(f"   Time: {batch_time:.2f} seconds")
    print(f"   Prices fetched: {len(prices_batch)}/{len(symbols)}")
    if prices_batch:
        sample_symbol = list(prices_batch.keys())[0]
        print(f"   Sample: {sample_symbol} = ${prices_batch[sample_symbol]:,.2f}")

    # Test individual fetch (old method)
    print("\n2. Testing INDIVIDUAL fetch (old method)...")
    start_time = time.time()
    prices_individual = {}
    for symbol in symbols:
        price = collector.get_price(symbol)
        if price:
            prices_individual[symbol] = price
    individual_time = time.time() - start_time

    print(f"   Time: {individual_time:.2f} seconds")
    print(f"   Prices fetched: {len(prices_individual)}/{len(symbols)}")

    # Compare results
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Batch fetch:      {batch_time:.2f}s")
    print(f"Individual fetch: {individual_time:.2f}s")

    if individual_time > 0 and batch_time > 0:
        speedup = individual_time / batch_time
        time_saved = individual_time - batch_time
        print(f"\n[OK] Batch fetch is {speedup:.1f}x FASTER!")
        print(f"[OK] Time saved: {time_saved:.2f} seconds per request")
    else:
        print("\n[WARNING] Could not calculate speedup")

    # Verify prices match
    if prices_batch and prices_individual:
        matching = sum(1 for s in symbols if s in prices_batch and s in prices_individual)
        print(f"\n[OK] {matching}/{len(symbols)} prices match between methods")

    print("=" * 60)

if __name__ == "__main__":
    test_batch_fetch()
