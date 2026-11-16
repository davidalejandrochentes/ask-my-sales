import re
from typing import Protocol

import httpx
from openai import APIError, OpenAI

from app.config import Settings


class LLMError(Exception):
    pass


class LLMClient(Protocol):
    def generate_sql(self, question: str, schema_context: str) -> str: ...


def _postprocess_response(raw_response: str) -> str:
    """Post-process LLM response: extract content, remove think blocks, remove fences, strip."""
    if not raw_response:
        return ""

    # 1. Use only the content field (already extracted by caller)
    content = raw_response

    # 2. Remove think blocks: ```question...answer```
    content = re.sub(r"```question.*?```", "", content, flags=re.DOTALL)

    # 3. Remove markdown fences: ```sql ... ``` or ``` ... ```
    content = re.sub(r"^```(?:sql)?\s*", "", content.strip(), flags=re.MULTILINE)
    content = re.sub(r"\s*```$", "", content.strip(), flags=re.MULTILINE)
    content = re.sub(r"^```\s*", "", content.strip(), flags=re.MULTILINE)
    content = re.sub(r"\s*```$", "", content.strip(), flags=re.MULTILINE)

    # 4. Strip whitespace
    content = content.strip()

    return content


class NvidiaLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.nvidia_api_key
        self.base_url = settings.nvidia_base_url
        self.model = settings.nvidia_model

        if not self.api_key or not self.model:
            raise LLMError("LLM not configured")

        http_client = httpx.Client(timeout=30.0)
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client,
        )

    def generate_sql(self, question: str, schema_context: str) -> str:
        system_prompt = self._build_system_prompt(schema_context)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=512,
            )
        except APIError as e:
            raise LLMError("LLM unavailable") from e
        except Exception as e:
            raise LLMError("LLM unavailable") from e

        if not response.choices or not response.choices[0].message.content:
            raise LLMError("Empty response from LLM")

        raw_content = response.choices[0].message.content
        processed = _postprocess_response(raw_content)

        if not processed:
            raise LLMError("Empty response after post-processing")

        return processed

    def _build_system_prompt(self, schema_context: str) -> str:
        return (
            "You are a SQL translator for SQLite. Convert natural language "
            "questions to SQL queries.\n\n"
            "Rules:\n"
            "- Return ONLY a single SELECT statement (WITH ... SELECT is allowed).\n"
            "- No explanations, no markdown, no code fences.\n"
            f"- Use only these tables/views:\n{schema_context}\n"
            "- Business rules:\n"
            '  - "ventas" or "vendimos" means status = \'completado\'.\n'
            "  - If no year specified, use the year from the data range.\n"
            "  - The sales_by_month_country.month column is in YYYY-MM format "
            "(e.g., '2025-03'). Filter with month = 'YYYY-MM' or "
            "strftime('%Y-%m', order_date) = 'YYYY-MM'.\n"
            "- If the question cannot be answered with the allowed tables, "
            "return a non-SQL response (it will be rejected)."
        )


def build_schema_context(conn) -> str:
    """Build schema context from the database."""
    lines = []

    # Get table schemas
    for table_name in ("orders", "sales_by_month_country", "top_customers"):
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        if cols:
            col_defs = ", ".join(f"{c[1]} {c[2]}" for c in cols)
            lines.append(f"  {table_name}({col_defs})")

    # Get distinct countries and statuses
    cursor = conn.execute("SELECT DISTINCT country FROM orders")
    countries = [row[0] for row in cursor.fetchall()]
    if countries:
        lines.append(f"  countries: {', '.join(sorted(countries))}")

    cursor = conn.execute("SELECT DISTINCT status FROM orders")
    statuses = [row[0] for row in cursor.fetchall()]
    if statuses:
        lines.append(f"  statuses: {', '.join(sorted(statuses))}")

    # Get date range
    cursor = conn.execute("SELECT MIN(order_date), MAX(order_date) FROM orders")
    row = cursor.fetchone()
    if row and row[0] and row[1]:
        lines.append(f"  date_range: {row[0]} to {row[1]}")

    return "\n".join(lines)


def get_llm_client(settings: Settings) -> LLMClient:
    return NvidiaLLMClient(settings)
