---
title: "RAG with ChromaDB — Retrieval-Augmented Generation from Scratch"
description: "Building a RAG pipeline over financial documents using ChromaDB and local Ollama for semantic retrieval without sending data to the cloud."
date: 2026-05-10
tags: [python, rag, chromadb, finance]
draft: true
---

# RAG with ChromaDB

RAG = retrieve relevant chunks from a document and pass them as context to the LLM. Ideal for financial reports or regulatory documentation.

## Pipeline

```python
from chromadb import Client
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def ingest_chunks(chunks: list[str], collection: str):
    chroma = Client()
    embeddings = model.encode(chunks)
    chroma.add(chunks, embeddings)

def retrieve(query: str, top_k: int = 5):
    q_emb = model.encode([query])
    return chroma.query(q_emb, top_k)
```

The chunking strategy directly impacts retrieval quality. For financial PDFs, chunks of around 512 tokens with 20% overlap usually work well.

## Why ChromaDB

- Pure Python, no Docker required
- Embeddings stored locally (no Pinecone costs)
- Built-in metadata filtering
- 5000 batch limit on inserts
