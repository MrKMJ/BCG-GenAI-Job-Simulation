import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "task2"))
from financial_chatbot import FinancialChatbot  # noqa: E402

bot = FinancialChatbot()


def test_total_revenue_latest_year():
    assert "$383.3 billion" in bot.respond("What is the total revenue of Apple?")


def test_specific_year():
    assert "$198.3 billion" in bot.respond("What are Microsoft's total liabilities in 2022?")


def test_net_income_change():
    answer = bot.respond("How has net income changed over the last year for Tesla?")
    assert "increased" in answer and "+19.4%" in answer


def test_comparison_ranks_apple_first():
    answer = bot.respond("Compare revenue across companies")
    assert answer.index("Apple") < answer.index("Microsoft") < answer.index("Tesla")


def test_unknown_metric_is_handled():
    assert bot.respond("What is Apple's stock price?").startswith("Sorry")


def test_missing_company_prompts_user():
    assert "Which company" in bot.respond("What is the net income?")


def test_out_of_range_year():
    assert "only have data" in bot.respond("Apple revenue in 2015")
