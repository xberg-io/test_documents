# Observability Toolkit

A lightweight toolkit for adding **metrics**, **traces**, and
**structured logs** to a service without wiring three separate
libraries. It exposes one initializer and one exporter, so
instrumentation stays out of your business logic.

## Features

- Structured logging with automatic request-scoped fields.
- Span-based tracing that propagates a `trace_id` across service calls.
- Counter, gauge, and histogram metrics with a shared registry.
- A single `/metrics` endpoint in Prometheus text format.

## Quick Start

Initialize the toolkit once at startup, then use the returned handle:

    let obs = observ::init("checkout-service");
    obs.counter("orders_total").increment();

The `init` call reads its exporter target from `OBSERV_ENDPOINT` and
falls back to standard output when the variable is unset.

## Signal Types

  -------------------------------------------------------------------------
  Signal      Use it for                           Cardinality rule
  ----------- ------------------------------------ ------------------------
  Counter     Monotonic event counts               Keep labels *bounded*

  Gauge       Values that rise and fall            Avoid per-request labels

  Histogram   Latency and size distributions       Pick buckets up front

  Log         Discrete, human-readable events      Never log secrets
  -------------------------------------------------------------------------

## Guidelines

Follow these rules to keep telemetry cheap and useful:

1.  Never put a user identifier in a metric label --- it explodes
    cardinality.
2.  Emit one span per logical operation, not one per function call.
3.  Log at `info` for state changes and `error` only for actionable
    failures.

Treat the `/metrics` endpoint as *internal* and keep it off the public
listener; scrape it from the private network only.
