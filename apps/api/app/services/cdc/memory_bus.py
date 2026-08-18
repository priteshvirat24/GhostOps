import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas.cdc import CDCEvent, CDCOperation, CDCProcessingStatus, CDCProcessingResult
from app.services.cdc.consumer import CockroachCDCConsumer
from app.core.logging import logger

class CDCMemoryBus:
    """
    Changefeed (CDC) Real-Time Memory Bus (§19.2).
    Delegates to CockroachCDCConsumer to process change events from CockroachDB changefeed stream,
    propagating trust score deltas, invalidating stale rankings, and updating institutional memory
    in real-time without database polling.
    """

    @classmethod
    def subscribe(cls, listener: Callable[[Dict[str, Any]], None]):
        def _wrapper(cdc_event: CDCEvent, res: CDCProcessingResult):
            listener({
                "table": cdc_event.source_table,
                "op": cdc_event.operation.value if hasattr(cdc_event.operation, "value") else str(cdc_event.operation),
                "row": cdc_event.payload,
                "result": res.model_dump()
            })
        CockroachCDCConsumer.subscribe(_wrapper)

    @classmethod
    def handle_changefeed_event(cls, event: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Processes a change event payload from CockroachDB CHANGEFEED.
        Event schema: {"table": "remediation_outcomes" | "institutional_memory_vectors", "op": "INSERT" | "UPDATE", "row": {...}}
        """
        table = event.get("table", "remediation_outcomes")
        row = event.get("row", {})
        op_str = event.get("op", "INSERT").upper()
        op = CDCOperation(op_str) if op_str in [e.value for e in CDCOperation] else CDCOperation.INSERT

        pk = row.get("id") or row.get("outcome_id") or row.get("memory_id") or f"pk-{uuid.uuid4().hex[:8]}"
        evt_id = event.get("event_id") or f"cdc-{table}-{pk}-{uuid.uuid4().hex[:6]}"

        cdc_evt = CDCEvent(
            event_id=evt_id,
            source_table=table,
            primary_key=str(pk),
            operation=op,
            payload=row,
            mode=event.get("mode", "TEST_EVENT_MODE")
        )

        res = CockroachCDCConsumer.consume_single_event(db, cdc_evt)
        return res.model_dump()
