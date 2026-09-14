@'
# Architectural Decision Log & Engineering Chronicle

Project: AppleSupport Autonomous Support Agent  
Environment: Python 3.10 | Conda (`hiver-env`) | Groq Inference Engine (`openai/gpt-oss-20b`)

---

## Decision 1: Thread Reconstruction and ID Normalization
* **Context:** The raw Kaggle TWCS dataset (`twcs.csv`) holds 2.8M flat rows. `in_response_to_tweet_id` contained floating-point values alongside string representations (`'12345.0'` vs `'12345'`).
* **Alternative Considered:** Direct string cast `str(row['in_response_to_tweet_id'])`.
* **Failure Mode Encountered:** Resulted in 0 built threads due to key-lookup misses (`'12345.0'` != `'12345'`).
* **Resolution:** Implemented `_normalize_id()` to cast float-like representations to integer strings: `str(int(float(val)))`. Built an iterative, cycle-safe graph walker that produced 82,101 conversation trees.

---

## Decision 2: Inference Backend Architecture (Groq LPU vs. Proprietary API)
* **Context:** Initial architecture called for OpenAI `gpt-4o-mini`. Need arose for zero-cost, high-speed execution.
* **Alternative Considered:** Local quantized models (Ollama/vLLM) vs. Groq cloud LPUs.
* **Resolution:** Integrated Groq's API utilizing `openai/gpt-oss-20b`.
* **Failure Mode Encountered:** Initial attempts on `llama-3.3-70b-versatile` yielded HTTP 404 access errors on free-tier keys. Programmatic probe revealed `openai/gpt-oss-20b` was actively provisioned and delivered sub-second structured JSON output.

---

## Decision 3: Intent Classification Baseline Hierarchy
* **Context:** Evaluating whether an LLM is justified over lightweight classical ML.
* **Architecture:** 3-tier benchmark:
  1. Trivial Baseline: Uniform Random Guessing (1/8 = 12.5% theoretical floor).
  2. Simple Baseline: N-gram TF-IDF (1,2) with balanced Logistic Regression.
  3. Main System: Few-shot prompt on `openai/gpt-oss-20b`.
* **Empirical Outcome:** Random achieved 13.33%, TF-IDF achieved 36.00% (Macro F1 0.2589), and the LLM achieved 50.00% (Macro F1 0.4196), demonstrating a +62.1% relative lift on long-tail categories.

---

## Decision 4: Dense Semantic Vector Indexing
* **Context:** Twitter support inquiries require grounded, concise responses reflecting authentic brand tone.
* **Architecture:** `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional dense vectors stored in a `faiss.IndexFlatIP` index over 5,063 real Apple conversation examples.
* **Reasoning:** Dense vectors capture semantic similarity across differing vocabularies (e.g., "phone won't turn on" vs. "black screen unresponsive").

---

## Decision 5: Guardrail Boundary Regex in Escalation
* **Context:** Substring matching `'media'` triggered a false positive escalation on `"Fix this immediately or I am suing"` because `"immediately"` contains `"media"`.
* **Resolution:** Upgraded keyword checks to require word-boundary regex patterns (`\b` + `re.escape(keyword)` + `\b`).

---

## Decision 6: The BLEU Metric Paradox in Generation
* **Observation:** Nearest-Neighbor retrieval scored higher BLEU (`0.2054`) than the Main Agent RAG pipeline (`0.1851`).
* **Analysis:** BLEU measures literal n-gram overlap. Nearest Neighbor returns exact historical tweets that duplicate boilerplate Twitter phrases ("DM us..."). The LLM synthesizes actionable, contextual diagnostic instructions, which lowers surface n-gram overlap while delivering higher practical utility.
'@ | Out-File -FilePath decision_log.md -Encoding utf8