# AppleSupport AI Support Agent

A production-style customer support assistant built for handling Apple-support-style conversations with intent classification, retrieval-augmented response generation, and escalation safeguards. The project demonstrates how an AI agent can triage customer messages, retrieve relevant historical cases, draft a grounded response, and decide when a case should be escalated to a human specialist.

## Overview

This project is designed for a support workflow where incoming messages may be routine requests, technical failures, account issues, or high-risk situations requiring human intervention. Instead of sending every message to a generic language model, the system applies a structured pipeline:

1. Detect the customer intent
2. Retrieve similar past support examples
3. Generate a customer-safe response grounded in retrieved evidence
4. Decide whether the issue should be auto-handled or escalated

The result is a hybrid AI support system that blends retrieval, language understanding, and operational guardrails.

## What this project does

The application is a support agent for AppleSupport-like conversations. It is meant to simulate a real-world helpdesk workflow in which the assistant:

- Classifies incoming customer messages into intents such as account access, device issues, how-to questions, safety concerns, and urgent escalation cases
- Uses a vector search index to find similar historical support threads or examples
- Generates a response using retrieved evidence instead of relying only on raw model memory
- Detects high-risk or escalation-worthy scenarios such as legal threats, safety hazards, abusive language, or urgent operational risk
- Provides a dashboard interface for testing and evaluating the system end-to-end

## Key features

- Intent classification pipeline with taxonomy-based categorization
- Retrieval-augmented generation (RAG) using FAISS vector search
- Semantic retrieval of relevant historical examples
- Escalation decision logic to prevent unsafe or inappropriate auto-replies
- Interactive Streamlit demo app for live testing
- Evaluation harness for checking system behavior on labeled examples
- Support for preset customer scenarios for quick testing
- Human-review flow for escalated cases

## Architecture

The project follows a modular agent pipeline:

- Intent layer: classifies the user message into a support category
- Reply layer: retrieves matching historical cases and produces an answer
- Escalation layer: decides whether the message needs human review or can be safely auto-handled
- App layer: exposes the workflow through a user-friendly dashboard

This design separates retrieval, classification, and decision-making so each component can be evaluated and improved independently.

## Folder structure

```text
hiver support agent/
├── app.py                          # Streamlit interface for the support agent
├── requirements.txt                # Project dependencies
├── README.md                       # Project documentation
├── decision_log.md                 # Decision logs and notes
├── EVALUATION_REPORT.md            # Evaluation summary/report
├── data/
│   ├── golden_eval/
│   │   └── golden_set.json         # Evaluation dataset
│   ├── processed/
│   │   ├── AppleSupport_all_tweets.csv
│   │   ├── AppleSupport_pairs.csv
│   │   └── AppleSupport/
│   │       ├── train.json
│   │       ├── train_labelled.json
│   │       ├── val.json
│   │       ├── test.json
│   │       └── threads.json
│   └── raw/
│       └── twcs.csv
├── eval/
│   ├── harness.py                  # Evaluation runner
│   ├── llm_judge.py               # Scoring/judging code
│   ├── metrics.py                 # Evaluation metrics
│   └── results/
│       └── evaluation_results.json
├── models/
│   └── embedding_index/
│       ├── examples.json
│       └── faiss.index
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_intent_design.ipynb
├── report/
├── src/
│   ├── agent.py                   # Main orchestration pipeline
│   ├── build_golden_set.py        # Golden dataset builder
│   ├── data_prep/
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   ├── prepare.py
│   │   └── thread_builder.py
│   ├── escalation/
│   │   └── decider.py
│   ├── intent/
│   │   ├── baseline_random.py
│   │   ├── baseline_tfidf.py
│   │   ├── classifier.py
│   │   ├── labeler.py
│   │   └── taxonomy.json
│   └── reply/
│       ├── baselines.py
│       ├── embedder.py
│       └── generator.py
└── .gitignore
```

## Tech stack

This project uses a modern Python ML and AI stack:

- Python 3
- Streamlit for the interactive dashboard
- FAISS for vector similarity search
- Sentence-transformers for embeddings
- scikit-learn for ML utilities and evaluation support
- Pandas and NumPy for data processing
- OpenAI-compatible LLM usage for classification and response generation
- PyTorch and Transformers ecosystem for model support
- Jupyter notebooks for exploration and experimentation

## Data and evaluation

The project includes support conversation datasets and evaluation infrastructure for checking quality and safety. It is designed around structured support interaction data, including labeled examples and golden evaluation sets.

The evaluation flow can help assess:

- Intent classification accuracy
- Reply relevance and helpfulness
- Whether dangerous or escalated cases are correctly routed
- Overall support-agent reliability

## Setup

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the Streamlit app:

```bash
streamlit run app.py
```

## Running the app

Once the dependencies are installed, launch the dashboard from the root directory:

```bash
streamlit run app.py
```

The app provides a panel for entering customer messages and running the full support pipeline. It also includes preset scenarios for testing common support cases, from routine how-to questions to serious risk escalations.

## Practical use case

This project is useful for learning and prototyping AI-powered support workflows. It demonstrates how an organization can combine:

- intent analysis
- similarity matching over historical cases
- grounded response generation
- realistic escalation controls

This makes it a strong example of an "AI support copilot" that is more controlled and operationally safer than a fully freeform chatbot.

## Notes

- The system is designed to balance automation with human oversight.
- Escalation logic is intentional: not every issue should be auto-resolved.
- The repository is suitable for experimentation, research, and extension to production-grade support workflows.

## Future improvements

Possible next steps include:

- adding a stronger feedback loop and human-in-the-loop review dashboard
- integrating with real CRM or ticketing systems
- improving model evaluation and guardrail logic
- expanding taxonomy and retrieval coverage
- adding logging, analytics, and monitoring for production deployment

## Summary

This project brings together modern AI tooling to create a support assistant that is practical, explainable, and safer for real-world use. It showcases a realistic pipeline for support triage, retrieval-based response generation, and compliance-aware escalation handling.
