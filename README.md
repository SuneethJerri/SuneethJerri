## Suneeth Jerri

I build data and ML systems, mostly in Python, and I care more about whether a
thing can be verified than whether it demos well.

Two habits show up in everything here. Constraints get enforced where they are
actually enforceable, not in a prompt or a comment. And a test that cannot fail
proves nothing, so the ones that matter get broken on purpose to check they
notice.

### Things I have built

**[tickerql](https://github.com/SuneethJerri/tickerql)** · Python, FastAPI, Postgres, React

Daily OHLCV for 135 assets across 19 sectors, with an agent you can ask
questions in plain English. It writes SQL, and it is physically incapable of
writing to the database: the agent's Postgres role has no `INSERT`, `UPDATE` or
`DELETE` grant, `default_transaction_read_only` is on, and `ALTER DEFAULT
PRIVILEGES` revokes future tables. 33 tests attack that boundary, each write
retried with the read-only flag turned off, because the role can turn it off
itself. Above the grants sit an sqlglot AST guard and a read-only transaction,
but the grants are the part that is not advice.

[Live](https://tickerql.vercel.app) · 277 backend tests · five generated chart
palettes, each searched against its own surface and checked for colour-vision
separation

**[rag-chatbot](https://github.com/SuneethJerri/rag-chatbot)** · Python

Retrieval-augmented chat over indexed documents. FAISS similarity search, YAML
configuration rather than hardcoded model parameters, 4-bit quantisation to keep
memory and latency down, and the pipeline split into a chunker, embedder,
retriever, LLM and orchestrator so any one of them can be swapped.

**[Object detection and tracking from a UAV](https://github.com/SuneethJerri/Object-Detection-and-Tracking-using-UAV)** · Python

An autonomous UAV that detects a target with YOLOv7, tracks it with SORT, and
follows it. Built with [@Akshat-vg](https://github.com/Akshat-vg).

### Tools

`Python` `SQL` `Postgres` `FastAPI` `PyTorch` `React` `TypeScript` `Docker`
