import os
import re
import calendar
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from jinja2 import Template

from db import run_read_query
from utils import is_select_only, contains_only_whitelisted_identifiers

#LangChain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load model + API key
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0
)

# -----------------------------
# PROMPT TEMPLATE
# -----------------------------
def get_prompt_template():
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Calculate last month
    if current_month == 1:
        last_month_year = current_year - 1
        last_month_num = 12
    else:
        last_month_year = current_year
        last_month_num = current_month - 1
    
    last_month = f"{last_month_year}-{last_month_num:02d}"
    
    return PromptTemplate(
        input_variables=["question"],
        template=f"""
You are a senior data analyst specialized in SQL generation.
Convert the user's question into a **pure SQL SELECT query** compatible with PostgreSQL.

Database schema:

financial_agent_balancesheets(
    id, month, total_assets, total_liabilities, equity, created_at
)
financial_agent_pl_reports(
    id, month, revenue, cost_of_goods_sold, operating_expenses, net_profit, created_at
)

Rules:
- Only generate valid SQL SELECT statements — no INSERT, UPDATE, or DELETE.
- Use correct table names based on requested columns:
  * financial_agent_balancesheets → total_assets, total_liabilities, equity
  * financial_agent_pl_reports → revenue, cost_of_goods_sold, operating_expenses, net_profit
- The column 'month' is stored as 'YYYY-MM' format.
- Current date context: Today is {current_year}-{current_month:02d}
- For "last month" queries, use: {last_month}
- For specific month names without year, use current year ({current_year})
- **Never use UNION or UNION ALL** unless absolutely necessary — and only if both queries have the same number and names of columns.
- If unsure, choose the **single table** that best matches the user's intent.
- NEVER include explanations, markdown, or extra text — return SQL only.
- Ensure SQL ends with a semicolon.

Examples:
Q: What was the revenue last month?
A: SELECT month, revenue FROM financial_agent_pl_reports WHERE month = '{last_month}';

Q: What was the net profit last month?
A: SELECT month, net_profit FROM financial_agent_pl_reports WHERE month = '{last_month}';

Q: What was the revenue in August?
A: SELECT month, revenue FROM financial_agent_pl_reports WHERE month = '{current_year}-08';

Q: Show total assets and equity for September
A: SELECT month, total_assets, equity FROM financial_agent_balancesheets WHERE month = '{current_year}-09';

Q: Compare revenue and net profit for July and August
A: SELECT month, revenue, net_profit FROM financial_agent_pl_reports WHERE month IN ('{current_year}-07', '{current_year}-08');

Now, based on these examples, generate a single SQL query for:
{{question}}
"""
    )


# -----------------------------
# SQL Validation
# -----------------------------
def validate_sql(candidate_sql: str) -> tuple[bool, str]:
    if not is_select_only(candidate_sql):
        return False, "Only SELECT statements allowed."
    if not contains_only_whitelisted_identifiers(candidate_sql):
        return False, "SQL references non-whitelisted tables/columns or unknown identifiers."
    return True, ""


# -----------------------------
# Helper: Date phrase parsing
# -----------------------------
def parse_date_range_from_text(text: str):
    t = text.lower()
    today = date.today()

    if "last month" in t:
        first = date(today.year, today.month, 1)
        prev = first - timedelta(days=1)
        return date(prev.year, prev.month, 1).isoformat(), prev.isoformat()

    if match := re.search(r"last\s+(\d+)\s+months?", t):
        n = int(match.group(1))
        end = today
        start = (today - relativedelta(months=n)).replace(day=1)
        return start.isoformat(), end.isoformat()

    if "last quarter" in t:
        q = (today.month - 1) // 3 + 1
        pq = q - 1
        year = today.year
        if pq == 0:
            pq = 4
            year -= 1
        start_month = 3 * (pq - 1) + 1
        start = date(year, start_month, 1)
        end = (start + relativedelta(months=3)) - timedelta(days=1)
        return start.isoformat(), end.isoformat()

    if "last year" in t:
        start = date(today.year - 1, 1, 1)
        end = date(today.year - 1, 12, 31)
        return start.isoformat(), end.isoformat()

    if match := re.search(r"([a-zA-Z]+)\s+(\d{{4}})", t):
        month_name, year = match.groups()
        try:
            month_num = list(calendar.month_name).index(month_name.capitalize())
            start = date(int(year), month_num, 1)
            from calendar import monthrange
            lastday = monthrange(int(year), month_num)[1]
            end = date(int(year), month_num, lastday)
            return start.isoformat(), end.isoformat()
        except ValueError:
            pass

    return None, None


# -----------------------------
# Main Execution Function
# -----------------------------
def run_question(question: str):
    try:
        # Create a fresh prompt template with current date context
        current_prompt_template = get_prompt_template()
        current_sql_chain = LLMChain(prompt=current_prompt_template, llm=llm)
        
        # Ask LangChain model for SQL
        response = current_sql_chain.invoke({"question": question})
        sql = response["text"].strip() if isinstance(response, dict) else str(response).strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        if not sql.lower().startswith("select"):
            raise ValueError(f"Invalid SQL generated: {sql}")
        if not sql.endswith(";"):
            sql += ";"

        # Validate SQL
        ok, reason = validate_sql(sql)
        if not ok:
            return {"ok": False, "error": f"Generated SQL rejected: {reason}", "sql": sql}

        # Handle possible date placeholders
        start, end = parse_date_range_from_text(question)
        params = {}
        if start and end:
            if ":start" in sql or ":end" in sql:
                params["start"], params["end"] = start, end
            else:
                sql = sql.replace("{start}", f"'{start}'").replace("{end}", f"'{end}'")

        # Run SQL query
        rows = run_read_query(sql, params)
        if not rows:
            return {"ok": True, "answer": "No data matched your query.", "sql": sql, "rows": []}

        # Format results
        if len(rows) == 1 and len(rows[0].keys()) == 1:
            k, v = list(rows[0].items())[0]
            answer = f"{k}: {v}"
        else:
            formatted = [
                ", ".join(f"{k}={v}" for k, v in r.items()) for r in rows[:5]
            ]
            if len(rows) > 5:
                formatted.append(f"... and {len(rows)-5} more rows")
            answer = "\n".join(formatted)

        return {"ok": True, "answer": answer, "sql": sql, "rows": rows}

    except Exception as e:
        return {"ok": False, "error": f"Processing error: {str(e)}"}
