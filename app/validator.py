import sqlglot
from sqlglot import exp


class InvalidSQLError(Exception):
    pass


ALLOWED_TABLES = {"orders", "sales_by_month_country", "top_customers"}
ALLOWED_FUNCTION_TYPES = {
    exp.Sum,
    exp.Count,
    exp.Avg,
    exp.Min,
    exp.Max,
    exp.Round,
    exp.TimeToStr,
    exp.Substring,
    exp.Lower,
    exp.Upper,
    exp.Coalesce,
    exp.Date,
    exp.Abs,
    exp.TsOrDsToTimestamp,
}


def validate_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise InvalidSQLError("Empty SQL")

    # 1. Reject comments
    if "--" in sql or "/*" in sql:
        raise InvalidSQLError("Comments are not allowed")

    # 2. Parse with sqlglot
    try:
        parsed = sqlglot.parse(sql, dialect="sqlite")
    except Exception as e:
        raise InvalidSQLError(f"Parse error: {e}") from e

    # 3. Exactly one statement (ignore empty trailing)
    non_empty = [s for s in parsed if s and not (isinstance(s, exp.Select) and not s.expressions)]
    if len(non_empty) != 1:
        raise InvalidSQLError("Exactly one statement required")

    stmt = non_empty[0]

    # 4. Root must be Select (allows CTE)
    if not isinstance(stmt, exp.Select):
        raise InvalidSQLError(f"Only SELECT statements are allowed, got {type(stmt).__name__}")

    # 5. Check for forbidden statement types in the tree
    forbidden_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Command,
        exp.Pragma,
        exp.Attach,
        exp.Union,
    )
    for node in stmt.walk():
        if isinstance(node, forbidden_types):
            raise InvalidSQLError(f"Forbidden statement type: {type(node).__name__}")

    # 6. Check tables (allow CTE aliases)
    cte_aliases = set()
    for cte in stmt.ctes or []:
        cte_aliases.add(cte.alias.lower())

    for node in stmt.walk():
        if isinstance(node, exp.Table):
            table_name = node.name.lower()
            if table_name not in ALLOWED_TABLES and table_name not in cte_aliases:
                raise InvalidSQLError(f"Table not allowed: {table_name}")

    # 7. Check functions
    for node in stmt.walk():
        if isinstance(node, exp.Anonymous):
            raise InvalidSQLError(f"Unknown function: {node.this}")
        if isinstance(node, exp.Func):
            if type(node) not in ALLOWED_FUNCTION_TYPES:
                raise InvalidSQLError(f"Function not allowed: {type(node).__name__}")

    # 8. Add LIMIT 1000 if missing
    if not stmt.args.get("limit"):
        stmt = stmt.limit(1000)

    return stmt.sql(dialect="sqlite")
