from typing import Optional
import math
from datetime import datetime, timezone
from app.core.config import settings

class StalenessCalculator:
    """
    Continuous exponential half-life staleness penalty calculator.
    Older historical incidents receive higher staleness penalties without being discarded.
    """

    @staticmethod
    def calculate_penalty(
        captured_at: datetime,
        reference_time: Optional[datetime] = None,
        half_life_days: Optional[int] = None
    ) -> float:
        if not captured_at:
            return 0.0

        ref_time = reference_time or datetime.now(timezone.utc)
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        age_seconds = max(0.0, (ref_time - captured_at).total_seconds())
        age_days = age_seconds / 86400.0

        hl_days = half_life_days or settings.STALENESS_DECAY_HALF_LIFE_DAYS
        if hl_days <= 0:
            return 0.0

        # Continuous exponential penalty factor from 0.0 (brand new) to 1.0 (very old)
        penalty = 1.0 - math.exp(- (age_days / hl_days) * math.log(2))
        return round(min(1.0, max(0.0, penalty)), 4)
