import time
import contextvars
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.core.logging import logger

# Context variables to track state per request
query_count = contextvars.ContextVar("query_count", default=0)
request_start_time = contextvars.ContextVar("request_start_time", default=0.0)

# Configuration
SLOW_QUERY_THRESHOLD_MS = 100.0  # Log queries taking longer than this
QUERY_COUNT_THRESHOLD = 10  # Warn if more than this many queries in one request


def setup_db_events(engine):
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        context._query_start_time = time.time()
        # Increment request-scoped query count
        count = query_count.get()
        query_count.set(count + 1)

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_time = (time.time() - context._query_start_time) * 1000

        if total_time > SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "slow_query_detected",
                duration_ms=round(total_time, 2),
                statement=(
                    statement[:500] + "..." if len(statement) > 500 else statement
                ),
                # parameters=str(parameters) # Be careful with sensitive data in logs
            )


def reset_query_count():
    query_count.set(0)


def get_query_count():
    return query_count.get()
