import uuid
import hashlib
import re
from typing import List
from sqlalchemy.orm import Session

from app.db.models import LearnedLesson, MemoryCandidate
from app.agents import get_model_provider
from app.core.logging import logger

class MemoryCandidateGenerator:
    """
    Memory Candidate Generator for GhostOps Stage 8.
    Converts extracted operational lessons into normalized candidate memory items with 1536-dim embeddings.
    Enforces security screening to prevent malicious or injected instructions from becoming active institutional memory.
    """

    MALICIOUS_PATTERNS = [
        r"(?i)drop\s+table",
        r"(?i)rm\s+-rf",
        r"(?i)sudo\s+",
        r"(?i)curl\s+https?://",
        r"(?i)eval\(",
        r"(?i)exec\(",
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)system_override",
        r"(?i)<script>",
        r"(?i)chmod\s+777",
        r"(?i)truncate\s+table"
    ]

    @classmethod
    def is_malicious(cls, text: str) -> bool:
        return any(re.search(pat, text) for pat in cls.MALICIOUS_PATTERNS)

    @classmethod
    def generate_candidates(
        cls,
        db: Session,
        lessons: List[LearnedLesson]
    ) -> List[MemoryCandidate]:
        provider = get_model_provider()
        candidates: List[MemoryCandidate] = []

        for lesson in lessons:
            norm_text = f"[{lesson.lesson_type}] {lesson.title}: {lesson.statement}".strip()
            fingerprint = hashlib.sha256(f"{lesson.incident_id}:{lesson.lesson_type}:{norm_text}".encode()).hexdigest()

            # Check if candidate fingerprint already exists (Idempotency)
            existing_cand = db.query(MemoryCandidate).filter(
                MemoryCandidate.normalized_fingerprint == fingerprint
            ).first()

            if existing_cand:
                candidates.append(existing_cand)
                continue

            # Generate 1536-dim embedding vector using active provider abstraction
            embedding_vec = provider.generate_embedding(norm_text)
            if len(embedding_vec) != 1536:
                # Ensure 1536-dim padding/truncation
                embedding_vec = (embedding_vec + [0.0] * 1536)[:1536]

            # Compute candidate quality score
            ev_has = len(lesson.supporting_evidence or []) > 0
            quality = round(min(0.99, (lesson.confidence * 0.5) + (0.4 if ev_has else 0.1) + 0.05), 4)

            # Security and Review Screening
            has_malicious = cls.is_malicious(norm_text) or any(cls.is_malicious(str(e)) for e in (lesson.supporting_evidence or []))
            needs_review = has_malicious or lesson.confidence < 0.70 or lesson.lesson_type == "NEGATIVE_KNOWLEDGE"

            status = "FLAGGED_FOR_REVIEW" if needs_review else "APPROVED"
            rejection_reason = "Malicious or untrusted instruction pattern detected." if has_malicious else None

            cand = MemoryCandidate(
                id=f"cand-{uuid.uuid4().hex[:12]}",
                lesson_id=lesson.id,
                candidate_text=norm_text,
                normalized_fingerprint=fingerprint,
                embedding=embedding_vec,
                source_incident_ids=[lesson.incident_id],
                source_execution_ids=[lesson.execution_id] if lesson.execution_id else [],
                evidence_refs=lesson.supporting_evidence or [],
                confidence=lesson.confidence if not has_malicious else 0.10,
                novelty_score=0.85,
                contradiction_score=0.9 if lesson.lesson_type == "NEGATIVE_KNOWLEDGE" else 0.0,
                applicability_score=0.90 if not has_malicious else 0.0,
                quality_score=quality if not has_malicious else 0.10,
                review_required=needs_review,
                rejection_reason=rejection_reason,
                status=status
            )

            db.add(cand)
            candidates.append(cand)

        db.commit()
        logger.info(f"[MemoryCandidateGenerator] Generated {len(candidates)} memory candidates with 1536-dim embeddings")
        return candidates
