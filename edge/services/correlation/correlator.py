from datetime import timedelta

from edge.domain.enums.severity import Severity
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.models.correlation_result import CorrelationResult
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.correlator import Correlator
from edge.helpers.severity_scale import raise_severity, lower_severity


WINDOW_SECONDS = 5
IMPORTANT_TAGS = ["Pumpa1.Radi", "Pumpa2.Radi", "Rezervoar.Kvar"]


class BasicCorrelator(Correlator):
    def __init__(self, telemetry_repository: TelemetryRepository):
        self.telemetry_repository = telemetry_repository

    def correlate(self, alert: SecurityAlert) -> CorrelationResult:
        window = timedelta(seconds=WINDOW_SECONDS)
        start = alert.timestamp - window
        end = alert.timestamp + window

        telemetry = self.telemetry_repository.get_between(start, end)

        score = 0
        details = {}

        if self._has_important_change(telemetry):
            score += 2
            details["process_change"] = True

        if alert.rule_id in ("RULE-002", "RULE-007"):
            score += 1
            details["critical_rule"] = alert.rule_id

        final_severity = self._apply_score(alert.severity, score)
        correlated = score > 0

        return CorrelationResult(
            score=score,
            final_severity=final_severity,
            correlated=correlated,
            details=details,
        )

    def _has_important_change(self, telemetry: list) -> bool:
        by_tag = {}
        for t in telemetry:
            if t.tag not in IMPORTANT_TAGS:
                continue
            by_tag.setdefault(t.tag, set()).add(t.value)

        for tag, values in by_tag.items():
            if len(values) > 1:
                return True
        return False

    def _apply_score(self, base: Severity, score: int) -> Severity:
        if score >= 2:
            return raise_severity(base, score - 1)
        if score == 0 and base == Severity.MEDIUM:
            return lower_severity(base, 2)
        return base