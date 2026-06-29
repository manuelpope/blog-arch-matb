---
title: "Outbox Pattern — Eventual Consistency in Payment Systems"
description: "How to guarantee that database operations and external events commit together, without distributed transactions."
date: 2026-01-15
tags: [architecture, payments, events, postgres]
draft: true
---

# Outbox Pattern

In payment systems, one of the most critical guarantees is: **if the transaction fails, no external event was emitted**. And vice versa: if everything commits, the event must be published.

The problem: a DB write + an external HTTP call are not atomic. If the HTTP call fails after commit, your system is in an inconsistent state.

## The Solution: Outbox Table

```
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  INSERT INTO outbox (event_type, payload) VALUES ('transfer', '{"from":1,"to":2,"amount":100}');
COMMIT;
-- Event loop reads the outbox and publishes to Kafka
```

This is implemented in PostgreSQL with Spring Boot and a background worker for event processing.
