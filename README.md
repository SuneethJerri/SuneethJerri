## Suneeth Jerri

M.Tech at IIIT Allahabad, in Robotics and Machine Intelligence. I work on
machine learning systems that have to hold up outside the benchmark: models
that keep working as the data shifts under them, and models that can be checked
rather than trusted.

Two habits show up in most of what is here. Constraints get enforced where they
are actually enforceable, not in a prompt or a comment. And a test that cannot
fail proves nothing, so the ones that matter get broken on purpose to confirm
they notice.

### Research

**Adaptive encrypted VPN traffic classification under concept drift** · M.Tech thesis, 2025 to present
`Python` `PyTorch` `Reinforcement Learning`

Classifying encrypted VPN traffic from a live stream, where the traffic keeps
changing and the labels arrive late or not at all. Two parts are the interesting
ones. Active learning with delayed labels, because in a real deployment you find
out whether you were right long after you had to decide. And an RL
meta-controller that treats query budget, retraining frequency and drift
adaptation as one joint decision rather than three separately tuned knobs.
Measured against flow-based transformer and online learning baselines.

**Attention-grounded regularization for vision-language models** · 2026 to present
`PyTorch` `Qwen2-VL` `LoRA` `GroundingDINO` `SAM`

Reducing object hallucination in Qwen2-VL by supervising *where* the model
looks, not just what it says. A BCE spatial alignment loss over token activation
maps pulls attention onto the region a mentioned object actually occupies.

- Hallucinated objects down by nearly half on CHAIR
- POPE precision up 9.82 points, 75.18% to 85.00%, with response fluency intact
- TAM-IoU from 0.0000 to 0.0135, which is the mechanism the other two numbers come from

Supervision at that granularity does not exist in captioning datasets, so it is
generated: COCO captions, NLTK noun extraction, GroundingDINO localization, SAM
mask refinement.

### Things I have built

**[tickerql](https://github.com/SuneethJerri/tickerql)** · `Python` `FastAPI` `Postgres` `React`

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

**[Target detection and tracking from a UAV](https://github.com/SuneethJerri/Object-Detection-and-Tracking-using-UAV)** · `YOLOv7` `SORT` `PixHawk` `OpenCV`

An autonomous UAV that detects and follows a ground target in real time, with
the whole tracking pipeline running on a Raspberry Pi 4. PixHawk and DroneKit
handle flight control and telemetry, including fail-safe return. Built with
[@Akshat-vg](https://github.com/Akshat-vg).

**[rag-chatbot](https://github.com/SuneethJerri/rag-chatbot)** · `Python` `FAISS`

Retrieval-augmented chat over indexed documents. YAML configuration rather than
hardcoded model parameters, 4-bit quantisation to keep memory and latency down,
and the pipeline split into a chunker, embedder, retriever, LLM and orchestrator
so any one of them can be swapped.

### Tools

**Languages** Python, C/C++, Java, JavaScript, SQL
**ML** PyTorch, Hugging Face, Transformers, Scikit-Learn, OpenCV, NumPy, Pandas
**Systems** Postgres, FastAPI, Django, React, Docker, Git, Linux, Wireshark

### Education

**IIIT Allahabad** · M.Tech, Information Technology (Robotics and Machine Intelligence) · 2025 to present · 8.17/10
**Keshav Memorial Institute of Technology, Hyderabad** · B.Tech, Computer Science and Engineering · 2020 to 2024 · 7.53/10

GATE 2025 qualified in both Computer Science and Data Science & AI. Deep
Learning Specialization, DeepLearning.AI.

### Contact

[LinkedIn](https://linkedin.com/in/suneeth-jerri) · suneeth47@gmail.com
