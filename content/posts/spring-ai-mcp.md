---
title: "Spring AI + MCP — Building Intelligent Agents"
description: "Integrating Model Context Protocol with Spring AI to give your local LLMs access to tools and external capabilities."
date: 2026-06-20
tags: [spring, ai, mcp, ollama]
draft: true
---

# Spring AI + MCP

The Model Context Protocol (MCP) lets an LLM interact with external tools. Spring AI supports it natively.

## Configuration

```java
@Bean
public ChatClient chatClient(ChatModel model) {
    return ChatClient.builder(model)
        .defaultTools(toolService)
        .build();
}
```

## Defining Tools

```java
public record GetBalanceRequest(@ToolParam Long accountId) {}

@Component
public class BankTools {
    @Tool(name = "get_balance", description = "Query account balance")
    public BigDecimal getBalance(Long accountId) {
        return accountRepo.findById(accountId).getBalance();
    }
}
```

The LLM decides when to invoke each tool based on the conversation context.
