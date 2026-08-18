import json
from typing import Optional, List, Any
from sqlalchemy.types import UserDefinedType, JSON
from sqlalchemy.engine.interfaces import Dialect

class CockroachVector(UserDefinedType):
    """
    Dialect-aware SQLAlchemy Type for CockroachDB Native VECTOR(dim) columns (§20, §26).
    Compiles to VECTOR(dim) on CockroachDB / PostgreSQL engines and falls back to JSON on SQLite.
    """

    def __init__(self, dim: int = 1536):
        self.dim = dim

    def get_col_spec(self, **kw: Any) -> str:
        return f"VECTOR({self.dim})"

    def bind_processor(self, dialect: Dialect):
        def process(value: Optional[List[float]]) -> Any:
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                if dialect.name in ("postgresql", "cockroachdb"):
                    # Format as vector literal '[x, y, z]' for CockroachDB VECTOR parsing
                    return f"[{','.join(str(float(x)) for x in value)}]"
                return list(value)
            return value
        return process

    def result_processor(self, dialect: Dialect, coltype: Any):
        def process(value: Any) -> Optional[List[float]]:
            if value is None:
                return None
            if isinstance(value, str):
                val_str = value.strip()
                if val_str.startswith("[") and val_str.endswith("]"):
                    items = val_str[1:-1].split(",")
                    return [float(x.strip()) for x in items if x.strip()]
                try:
                    return json.loads(val_str)
                except Exception:
                    return None
            if isinstance(value, (list, tuple)):
                return [float(x) for x in value]
            return value
        return process

def VectorType(dim: int = 1536):
    """Factory creating a CockroachVector with SQLite JSON fallback."""
    return CockroachVector(dim=dim).with_variant(JSON, "sqlite")
