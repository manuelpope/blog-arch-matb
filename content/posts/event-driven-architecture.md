---
title: "Event-Driven Architecture: From Monolith to Microservices"
description: "How event-driven patterns enable clean service boundaries, eventual consistency, and horizontal scaling in distributed financial systems."
date: 2026-06-15
tags: [architecture, kafka, microservices, events]
draft: false
---

## The Problem with Synchronous Calls

In a monolith, a single HTTP call can chain through multiple modules in one transaction. Move to microservices and that chain becomes a distributed graph of synchronous calls — brittle, tightly coupled, and impossible to scale independently.

The alternative: **decouple via events**.

```mermaid
graph LR
    A[Client] -->|HTTP POST| B[Order Service]
    B -->|INSERT| C[(DB)]
    B -->|emit| D[(Event Bus)]
    D -->|consume| E[Inventory Service]
    D -->|consume| F[Payment Service]
    D -->|consume| G[Notification Service]
    E -->|UPDATE| H[(DB)]
    F -->|AUTHORIZE| I[(Payment Gateway)]
    G -->|SEND| J[(Email/SMS)]
```

Each service owns its data and reacts to events. No service calls another directly — they all listen to the bus.

## The Outbox Pattern: Guaranteeing At-Least-Once Delivery

The hard problem: a database write and an event publish can't be atomic across process boundaries. If the HTTP call to the broker fails after the DB commit, you're in an inconsistent state.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    participant Worker
    participant Broker

    Client->>API: POST /orders
    API->>DB: BEGIN
    DB->>DB: INSERT order + INSERT outbox_entry
    DB-->>API: COMMIT
    API-->>Client: 201 Created

    Worker->>DB: SELECT PENDING outbox
    DB-->>Worker: [entry]
    Worker->>Broker: PUBLISH event
    Broker-->>Worker: OK
    Worker->>DB: UPDATE status = PUBLISHED
```

The key insight: the DB write and the outbox write are in the **same transaction**. Either both succeed or neither does. The worker polls the outbox table and retries until the broker acknowledges.

## CQRS: Separating Reads from Writes

Command Query Responsibility Segregation solves the read/write conflict in event-driven systems. Your write model is optimized for transactions. Your read model is optimized for queries.

```mermaid
graph TD
    A[Write Side<br/>POST /orders] -->|Events| B[(Event Store)]
    B -->|Project| C[Read Model 1<br/>GET /orders/history]
    B -->|Project| D[Read Model 2<br/>GET /inventory]
    B -->|Project| E[Read Model 3<br/>GET /dashboard]
```

Event sourcing takes this further: instead of storing current state, you store the sequence of events that produced it. The current state is a replay.

## Saga Pattern: Managing Distributed Transactions

ACID transactions don't span services. When a business operation requires multiple services to participate, you need a coordination strategy.

```mermaid
sequenceDiagram
    participant Orchestrator
    participant OrderSvc
    participant PaymentSvc
    participant InventorySvc
    participant FulfillmentSvc

    Orchestrator->>OrderSvc: createOrder()
    OrderSvc-->>Orchestrator: OrderCreated
    Orchestrator->>PaymentSvc: chargeCustomer()
    PaymentSvc-->>Orchestrator: PaymentAuthorized
    Orchestrator->>InventorySvc: reserveItems()
    InventorySvc-->>Orchestrator: ItemsReserved
    Orchestrator->>FulfillmentSvc: scheduleShipment()
    FulfillmentSvc-->>Orchestrator: ShipmentScheduled
    Orchestrator->>OrderSvc: confirmOrder()
```

If any step fails, the orchestrator issues compensating transactions to rollback: refund the payment, release the inventory reservation, cancel the shipment.

## Choosing Your Broker

| Broker | Durability | Replay | Ordering | Best For |
|--------|-----------|--------|----------|---------|
| **Kafka** | Persistent | From offset | Per partition | High-throughput, replay-heavy workloads |
| **RabbitMQ** | Optional | No | Per queue | Task queues, fan-out patterns |
| **Redis Pub/Sub** | Fire-and-forget | No | Per channel | MVP, low-latency, local dev |
| **SQS** | Persistent | Via visibility timeout | Best-effort | AWS-native, serverless |

For a financial system processing millions of transactions daily, **Kafka** is the clear choice. For a quick prototype or local development, **Redis Pub/Sub** gets you running in minutes.

## Conclusion

Event-driven architecture trades the simplicity of ACID transactions for the scalability of eventual consistency. The patterns exist to manage that tradeoff:

- **Outbox Pattern** for reliable event publication
- **Saga Pattern** for distributed transaction coordination
- **CQRS** for separating read and write concerns
- **Event Sourcing** for auditability and replay

The complexity is real, but so is the gain: services that scale independently, systems that survive partial failures, and architectures that evolve with the business.
