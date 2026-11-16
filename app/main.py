from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.db import connect_ro, run_query
from app.llm import LLMError, build_schema_context, get_llm_client
from app.validator import InvalidSQLError, validate_sql

app = FastAPI()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class AskResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def get_validated_settings() -> Settings:
    settings = get_settings()
    if not settings.nvidia_api_key or not settings.nvidia_model:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "LLM_NOT_CONFIGURED", "message": "LLM not configured"}},
        )
    return settings


@app.get("/health", response_model=dict[str, str])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/ask",
    response_model=AskResponse,
    responses={
        422: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def ask(
    request: AskRequest,
    settings: Settings = Depends(get_validated_settings),  # noqa: B008
) -> AskResponse:
    llm = get_llm_client(settings)
    db_path = settings.db_path

    # Build schema context
    schema_context = ""
    try:
        conn = connect_ro(db_path)
        schema_context = build_schema_context(conn)
        conn.close()
    except Exception:
        schema_context = "orders(order_id, order_date, customer, country, product, amount, status)"

    # Call LLM
    try:
        sql = llm.generate_sql(request.question, schema_context)
    except LLMError as e:
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "LLM_UNAVAILABLE", "message": str(e)}},
        ) from e

    # Validate SQL
    try:
        validated_sql = validate_sql(sql)
    except InvalidSQLError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_SQL", "message": str(e)}},
        ) from e

    # Execute on read-only connection
    try:
        conn = connect_ro(db_path)
        columns, rows = run_query(conn, validated_sql)
        conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "SQL_EXECUTION_ERROR", "message": str(e)}},
        ) from e

    return AskResponse(
        question=request.question,
        sql=validated_sql,
        columns=columns,
        rows=[list(row) for row in rows],
        row_count=len(rows),
    )
