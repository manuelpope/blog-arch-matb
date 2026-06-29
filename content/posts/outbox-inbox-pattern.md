---
title: "Outbox & Inbox Patterns — Distributed Transactions in Banking"
description: "Production-grade implementation of Transactional Outbox and Inbox patterns in Python, PostgreSQL, and Redis for distributed banking transactions with exactly-once semantics."
date: 2026-06-29
tags: [architecture, distributed-systems, outbox-pattern, python, postgresql, redis, saga]
draft: false
---

# A Microservices Architecture for Distributed Banking Transactions Using the Transactional Outbox and Inbox Patterns

**Manuel Tobon**
*Senior Backend Engineer*
*manuelpope@gmail.com*

---

## Abstract

This paper presents a comprehensive analysis of a Python-based microservice system that implements the Transactional Outbox and Inbox patterns for distributed banking transactions. The system comprises two independently deployed microservices — an Outbox Pattern producer service (port 5001) and an Inbox Pattern consumer service (port 5002) — sharing a PostgreSQL database and a Redis Pub/Sub message broker. The Outbox service atomically writes a banking transaction and a corresponding outbox event entry in a single database transaction, guaranteeing at-least-once event delivery. The Inbox service subscribes to those channels and processes each event inside a database transaction that atomically inserts an inbox deduplication row alongside a business-side saga step record, thereby achieving exactly-once processing semantics.

**Index Terms** — Transactional Outbox Pattern, Inbox Pattern, exactly-once processing, at-least-once delivery, PostgreSQL, Redis Pub/Sub, Python, SQLAlchemy, saga pattern, microservice architecture

## 1. Introduction

Distributed systems face a fundamental challenge: database writes and message broker publications cannot be performed atomically. If a service writes to its database and then publishes a message to a broker, a crash between those two operations produces either a committed transaction with no published event (downstream systems never learn of the change) or a published event with no committed transaction (downstream systems act on data that does not exist). This inconsistency is known as the dual-write problem.

The Transactional Outbox Pattern addresses the first half of this problem by writing the business entity and the outbox event entry in a single database transaction. A separate worker polls the outbox table and publishes events to the broker, retrying as needed. This guarantees at-least-once delivery because the event persists in the outbox table until the worker successfully publishes and marks it.

The Transactional Inbox Pattern addresses the second half: when a consumer receives a message from a broker that offers only at-least-once delivery semantics, the consumer must ensure the message's business effect is applied exactly once.

## 2. Related Technologies

The system is built on a deliberately lean technology stack chosen for operational simplicity.

**PostgreSQL 16** serves as the sole database. PostgreSQL was selected for its native `FOR UPDATE SKIP LOCKED` support, which enables multiple worker processes to claim distinct outbox entries concurrently.

**Redis 7** is used exclusively as a Pub/Sub broker. Redis Pub/Sub provides sub-millisecond publish latency and zero-setup operational overhead.

**Python 3.12** is the implementation language with Flask 3.1, SQLAlchemy 2.0, Pydantic v2, structlog, and prometheus-client.

## 3. System Overview

The system implements a cross-country banking transaction saga. A client in Country A submits a transaction via HTTP. The Outbox Pattern service persists the transaction and emits a `TransactionCreated` event to Redis.

## 4. The Outbox Algorithm

The CTE-based claim algorithm uses PostgreSQL's `FOR UPDATE SKIP LOCKED` to perform three operations in a single database round-trip:

1. **SELECT** up to `batch_size` pending entries ordered by `created_at` (FIFO)
2. **UPDATE** those entries to `status = PROCESSING`
3. **RETURNING** the entry data

The `FOR UPDATE SKIP LOCKED` clause instructs PostgreSQL to skip rows that are locked by other transactions, allowing multiple worker replicas to process batches in parallel without blocking or duplicating work.

## 5. The Inbox Algorithm

When a message arrives at the inbox worker, it is processed inside a single database transaction:

1. Insert the inbox deduplication row with `message_id` as the primary key
2. Execute the business handler in the same transaction
3. Mark the inbox row as processed

If the same message is delivered twice, the second insertion collides on the primary key, rolls back, and produces no duplicate business effect. This is the exactly-once guarantee.

## 6. Correctness Arguments

The outbox and inbox patterns compose to provide a complete correctness guarantee: every committed transaction produces exactly one saga step record downstream, despite the broker offering only at-least-once delivery.

## 7. Operational Tradeoffs

Redis Pub/Sub does not persist messages. If the inbox worker is disconnected, messages published during the disconnect window are lost. The system mitigates this through the outbox's retry mechanism. A future migration to Apache Kafka would provide durability and replay capability.

## 8. Conclusion

This implementation demonstrates that reliable distributed transaction processing can be achieved through the composition of the outbox and inbox patterns without distributed transaction coordinators, provided that the database serves as the source of truth for both the business entity and the event deduplication log.
