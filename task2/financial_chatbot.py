"""
BCG X GenAI Job Simulation — Task 2
Rule-based financial chatbot built on the 10-K data analysed in Task 1.

Usage:
    python financial_chatbot.py            # interactive chat
    python financial_chatbot.py --demo     # run the predefined demo queries
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "financial_analysis.csv"

COMPANY_ALIASES = {
    "Microsoft": ["microsoft", "msft"],
    "Tesla": ["tesla", "tsla"],
    "Apple": ["apple", "aapl"],
}

# intent -> (keywords, dataframe column, human label)
METRIC_INTENTS = {
    "revenue": (["revenue", "sales", "top line", "turnover"], "Total Revenue", "total revenue"),
    "net_income": (["net income", "profit", "earnings", "bottom line"], "Net Income", "net income"),
    "assets": (["asset"], "Total Assets", "total assets"),
    "liabilities": (["liabilit", "debt"], "Total Liabilities", "total liabilities"),
    "cash_flow": (["cash flow", "operating cash", "cash from operations", "ocf"],
                  "Cash Flow from Operating Activities", "operating cash flow"),
    "margin": (["margin", "profitability"], "Net Profit Margin (%)", "net profit margin"),
    "debt_to_equity": (["debt-to-equity", "debt to equity", "leverage", "d/e"],
                       "Debt-to-Equity (x)", "debt-to-equity ratio"),
}
GROWTH_COLS = {
    "Total Revenue": "Total Revenue Growth (%)",
    "Net Income": "Net Income Growth (%)",
    "Total Assets": "Total Assets Growth (%)",
    "Total Liabilities": "Total Liabilities Growth (%)",
    "Cash Flow from Operating Activities": "Operating Cash Flow Growth (%)",
}
CHANGE_WORDS = ["change", "grow", "growth", "increase", "decrease", "trend", "over the last", "compared to last"]
COMPARE_WORDS = ["compare", "comparison", "versus", " vs", "which company", "highest", "lowest", "best", "rank"]

HELP_TEXT = """I can answer questions about Microsoft, Tesla and Apple (FY2021–FY2023, from their 10-K filings). Try:
  • What is the total revenue of Apple?
  • How has net income changed over the last year for Tesla?
  • What are Microsoft's total liabilities in 2022?
  • What is Tesla's operating cash flow?
  • What is Apple's net profit margin?
  • Compare revenue across companies
  • Give me a summary of Microsoft
Type 'exit' to quit."""


def fmt_money(millions: float) -> str:
    return f"${millions / 1000:,.1f} billion" if abs(millions) >= 1000 else f"${millions:,.0f} million"


def fmt_value(column: str, value: float) -> str:
    if column.endswith("(%)"):
        return f"{value:.1f}%"
    if column.endswith("(x)"):
        return f"{value:.2f}x"
    return fmt_money(value)


class FinancialChatbot:
    def __init__(self, data_path: Path = DATA_PATH):
        self.df = pd.read_csv(data_path)
        self.years = sorted(self.df["Fiscal Year"].unique())
        self.latest_year = self.years[-1]

    # ---------- parsing ----------
    @staticmethod
    def _find_companies(q: str) -> list[str]:
        return [c for c, aliases in COMPANY_ALIASES.items() if any(a in q for a in aliases)]

    def _find_year(self, q: str) -> int | None:
        m = re.search(r"\b(20\d{2})\b", q)
        return int(m.group(1)) if m else None

    @staticmethod
    def _find_metric(q: str) -> str | None:
        # check the more specific intents first (e.g. "debt to equity" before "debt")
        for intent in ["debt_to_equity", "margin", "cash_flow", "net_income", "revenue", "assets", "liabilities"]:
            if any(k in q for k in METRIC_INTENTS[intent][0]):
                return intent
        return None

    def _row(self, company: str, year: int) -> pd.Series | None:
        r = self.df[(self.df["Company"] == company) & (self.df["Fiscal Year"] == year)]
        return None if r.empty else r.iloc[0]

    # ---------- answers ----------
    def _point_answer(self, company: str, intent: str, year: int) -> str:
        _, col, label = METRIC_INTENTS[intent]
        row = self._row(company, year)
        if row is None:
            return f"I only have data for fiscal years {self.years[0]}–{self.latest_year}."
        verb = "were" if label.endswith(("assets", "liabilities")) else "was"
        return f"{company}'s {label} in fiscal {year} {verb} {fmt_value(col, row[col])}."

    def _change_answer(self, company: str, intent: str, year: int) -> str:
        _, col, label = METRIC_INTENTS[intent]
        cur, prev = self._row(company, year), self._row(company, year - 1)
        if cur is None or prev is None:
            return f"I need two consecutive years to measure change; available years are {self.years[0]}–{self.latest_year}."
        diff = cur[col] - prev[col]
        direction = "increased" if diff > 0 else "decreased" if diff < 0 else "was unchanged"
        if col.endswith("(%)") or col.endswith("(x)"):
            unit = " percentage points" if col.endswith("(%)") else "x"
            return (f"{company}'s {label} {direction} from {fmt_value(col, prev[col])} in {year - 1} "
                    f"to {fmt_value(col, cur[col])} in {year} ({diff:+.2f}{unit}).")
        pct = cur[GROWTH_COLS[col]]
        return (f"{company}'s {label} {direction} from {fmt_money(prev[col])} in {year - 1} to "
                f"{fmt_money(cur[col])} in {year}, a change of {pct:+.1f}%.")

    def _compare_answer(self, intent: str, year: int) -> str:
        _, col, label = METRIC_INTENTS[intent]
        sub = self.df[self.df["Fiscal Year"] == year].sort_values(col, ascending=False)
        lines = [f"{i}. {r['Company']}: {fmt_value(col, r[col])}" for i, (_, r) in enumerate(sub.iterrows(), 1)]
        return f"Fiscal {year} {label}, highest to lowest:\n  " + "\n  ".join(lines)

    def _summary_answer(self, company: str, year: int) -> str:
        r = self._row(company, year)
        return (f"{company} — fiscal {year} snapshot:\n"
                f"  Revenue: {fmt_money(r['Total Revenue'])} ({r['Total Revenue Growth (%)']:+.1f}% YoY)\n"
                f"  Net income: {fmt_money(r['Net Income'])} ({r['Net Income Growth (%)']:+.1f}% YoY)\n"
                f"  Net margin: {r['Net Profit Margin (%)']:.1f}%\n"
                f"  Total assets: {fmt_money(r['Total Assets'])} | Total liabilities: {fmt_money(r['Total Liabilities'])}\n"
                f"  Operating cash flow: {fmt_money(r['Cash Flow from Operating Activities'])}\n"
                f"  Debt-to-equity: {r['Debt-to-Equity (x)']:.2f}x")

    def respond(self, query: str) -> str:
        q = " " + query.lower().strip() + " "
        if not query.strip():
            return "Please type a question, or 'help' for examples."
        if any(w in q for w in [" help ", " hi ", " hello ", " hey ", "what can you"]):
            return HELP_TEXT

        companies = self._find_companies(q)
        intent = self._find_metric(q)
        year = self._find_year(q) or self.latest_year

        if year not in self.years:
            return f"Sorry, I only have data for fiscal years {self.years[0]}–{self.latest_year}."

        if any(w in q for w in ["summary", "overview", "snapshot", "tell me about"]) and companies:
            return "\n\n".join(self._summary_answer(c, year) for c in companies)

        if intent is None:
            return ("Sorry, I can only answer questions about revenue, net income, assets, liabilities, "
                    "operating cash flow, profit margin and debt-to-equity. Type 'help' for examples.")

        if any(w in q for w in COMPARE_WORDS) or len(companies) > 1 or (not companies and "compan" in q):
            return self._compare_answer(intent, year)

        if not companies:
            return "Which company do you mean — Microsoft, Tesla or Apple?"

        if any(w in q for w in CHANGE_WORDS):
            if year == self.years[0]:
                year = self.years[1]
            return "\n".join(self._change_answer(c, intent, year) for c in companies)

        return "\n".join(self._point_answer(c, intent, year) for c in companies)


DEMO_QUERIES = [
    "What is the total revenue of Apple?",
    "How has net income changed over the last year for Tesla?",
    "What are Microsoft's total liabilities in 2022?",
    "What is Tesla's operating cash flow?",
    "What is Apple's net profit margin?",
    "Compare revenue across companies",
    "How has Microsoft's cash flow changed?",
    "Give me a summary of Microsoft",
    "What is Apple's stock price?",
]


def main() -> None:
    bot = FinancialChatbot()
    if "--demo" in sys.argv:
        for q in DEMO_QUERIES:
            print(f"You: {q}\nBot: {bot.respond(q)}\n")
        return
    print("BCG GenAI Financial Chatbot\n" + HELP_TEXT + "\n")
    while True:
        try:
            q = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if q.strip().lower() in {"exit", "quit", "bye"}:
            print("Bot: Goodbye!")
            break
        print("Bot:", bot.respond(q), "\n")


if __name__ == "__main__":
    main()
