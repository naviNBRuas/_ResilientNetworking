from __future__ import annotations

import threading
from observability_policy_hub import MetricRegistry, PolicyDecision, PolicyEngine


def test_metrics_summary():
    m = MetricRegistry()
    m.inc("requests", 2)
    m.set_gauge("inflight", 3)
    m.observe("lat", 0.1)
    m.observe("lat", 0.2)
    summary = m.summary()
    assert summary["counters"]["requests"] == 2
    assert summary["gauges"]["inflight"] == 3
    assert summary["histograms"]["lat"]["count"] == 2
    assert abs(summary["histograms"]["lat"]["avg"] - 0.15) < 1e-9
    assert summary["histograms"]["lat"]["p50"] == 0.2  # sorted: [0.1, 0.2], index 1 -> 0.2
    assert summary["histograms"]["lat"]["p99"] == 0.2


def test_metrics_histogram_window():
    window_size = 10
    m = MetricRegistry(histogram_window_size=window_size)
    for i in range(20):
        m.observe("vals", i)
    
    summary = m.summary()
    assert summary["histograms"]["vals"]["count"] == 10
    # Should contain 10..19
    assert summary["histograms"]["vals"]["avg"] == sum(range(10, 20)) / 10


def test_metrics_concurrency():
    m = MetricRegistry()
    
    def worker():
        for _ in range(100):
            m.inc("concurrent_counter")
            m.observe("concurrent_hist", 1.0)
            
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    summary = m.summary()
    assert summary["counters"]["concurrent_counter"] == 1000
    assert summary["histograms"]["concurrent_hist"]["count"] == 1000


def test_policy_engine_blocks():
    engine = PolicyEngine()

    def deny_if_too_many(ctx):
        if ctx.get("inflight", 0) > 5:
            return PolicyDecision(allow=False, reason="overload")
        return PolicyDecision(allow=True)

    engine.register_rule("overload", deny_if_too_many)
    assert engine.evaluate({"inflight": 1}).allow is True
    decision = engine.evaluate({"inflight": 10})
    assert decision.allow is False
    assert "overload" in decision.reason


def test_policy_engine_fail_closed():
    # Default is fail_open=False
    engine = PolicyEngine(fail_open=False)
    
    def crashing_rule(ctx):
        raise ValueError("Boom")
        
    engine.register_rule("crasher", crashing_rule)
    
    decision = engine.evaluate({})
    assert decision.allow is False
    assert "error-in-rule:crasher" in decision.reason


def test_policy_engine_fail_open():
    engine = PolicyEngine(fail_open=True)
    
    def crashing_rule(ctx):
        raise ValueError("Boom")
        
    engine.register_rule("crasher", crashing_rule)
    
    decision = engine.evaluate({})
    assert decision.allow is True