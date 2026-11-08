# Financial Chatbot — Documentation (Task 2)

## Overview
A rule-based prototype chatbot that answers natural-language questions about the financial performance of **Microsoft, Tesla and Apple** for fiscal years 2021–2023. It uses the dataset extracted and analysed in Task 1 (`data/financial_analysis.csv`), so every answer is traceable to the companies' 10-K filings.

## How it works
1. **Load data** — the Task 1 output (raw metrics + YoY growth + ratios) is loaded into a pandas DataFrame at start-up.
2. **Parse the query** — lower-cased text is scanned for:
   - **Company** (name or ticker: `apple`/`aapl`, `microsoft`/`msft`, `tesla`/`tsla`)
   - **Metric intent** via keyword lists (e.g. *revenue / sales*, *net income / profit / earnings*, *cash flow*, *margin*, *debt-to-equity*)
   - **Fiscal year** (any `20XX`; defaults to the latest year, 2023)
   - **Question type** — point value, change over time, cross-company comparison, or company summary
3. **Respond** — the matching row(s) are looked up and a formatted sentence is returned. Pre-computed growth rates mean no calculation is needed at query time.
4. **Fallbacks** — unknown metrics, missing company, or out-of-range years return a helpful message instead of a wrong answer.

## Supported queries (examples)
| Query | Type |
|---|---|
| What is the total revenue of Apple? | Point value |
| How has net income changed over the last year for Tesla? | Change |
| What are Microsoft's total liabilities in 2022? | Point value, specific year |
| What is Tesla's operating cash flow? | Point value |
| What is Apple's net profit margin? | Ratio |
| Compare revenue across companies | Comparison |
| Give me a summary of Microsoft | Summary |

## Running it
```bash
pip install -r requirements.txt
python task2/financial_chatbot.py          # interactive
python task2/financial_chatbot.py --demo   # predefined queries
pytest tests                               # tests
```

## Limitations
- **Keyword matching, not NLU** — phrasing outside the keyword lists (or typos) is not understood.
- **Fixed scope** — three companies, five core metrics plus derived ratios, FY2021–FY2023 only; no quarterly (10-Q) data.
- **No context memory** — each question is answered independently ("what about Tesla?" won't reuse the previous metric).
- **Static data** — figures must be refreshed manually when new filings are released.
- **No qualitative insight** — it reports numbers but cannot explain *why* they moved (e.g. Tesla's FY23 deferred-tax benefit).

## Next steps toward a GenAI solution
- Replace keyword parsing with an LLM for intent/entity extraction, keeping the DataFrame as the single source of truth for numbers (avoids hallucinated figures).
- Add retrieval (RAG) over the 10-K/10-Q text (MD&A, risk factors) to answer "why" questions with citations.
- Automate ingestion from SEC EDGAR's XBRL API to cover more companies and quarters.
- Add conversation memory and a web UI (e.g. Flask/Streamlit).
