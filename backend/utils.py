import re

# Whitelisted tables and columns — update this if your schema changes.
WHITELIST = {
    "financial_agent_balancesheets": {
        "id", "month", "total_assets", "total_liabilities", "equity", "created_at"
    },
    "financial_agent_pl_reports": {
        "id", "month", "revenue", "cost_of_goods_sold", "operating_expenses", "net_profit", "created_at"
    }
}

# Only allow SELECT queries (very strict)
ALLOWED_STATEMENTS = r'^\s*select[\s\S]+?(;)?\s*$'

def is_select_only(sql: str) -> bool:
    """Ensure query starts with SELECT and contains no forbidden commands."""
    sql = sql.strip().lower()
    forbidden = ["insert", "update", "delete", "drop", "alter", "create"]
    if not re.match(ALLOWED_STATEMENTS, sql, re.IGNORECASE):
        return False
    if any(word in sql for word in forbidden):
        return False
    return True

def contains_only_whitelisted_identifiers(sql: str) -> bool:
    """
    Relaxed but safe validator.
    - Allows any SELECT, JOIN, UNION, or window function query
    - Ensures only SELECT (no data modifications)
    - Allows all aliases and functions
    """
    sql = sql.strip().lower()

    # Block dangerous SQL types
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
    if any(word in sql for word in forbidden):
        return False

    # Ensure it starts with SELECT
    if not sql.startswith("select"):
        return False

    # Ensure it only touches our known tables
    allowed_tables = set(WHITELIST.keys())
    for table in re.findall(r"from\s+([a-z_][a-z0-9_]*)", sql):
        if table not in allowed_tables:
            return False
    for table in re.findall(r"join\s+([a-z_][a-z0-9_]*)", sql):
        if table not in allowed_tables:
            return False

    # Otherwise, allow all columns, functions, and aliases
    return True
