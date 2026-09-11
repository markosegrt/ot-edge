from datetime import timedelta

from edge.domain.enums.severity import Severity
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.models.correlation_result import CorrelationResult
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.correlator import Correlator
from edge.helpers.severity_scale import raise_severity, lower_severity


WINDOW_SECONDS = 5
# Sabotaza ima odlozenu posledicu: upis zatvori ventil, pritisak raste par
# sekundi. Zato opasnu vrednost gledamo u SIREM prozoru UNAPRED od upisa.
DANGER_LOOKAHEAD_SECONDS = 15

# Prekidacki tagovi (pali/gasi, kvar) — menjaju se samo kad se nesto desi.
# Namerno BEZ Nivo/Pritisak jer oni stalno lebde (bili bi lazna promena).
IMPORTANT_TAGS = [
    # PLC1 (pumpe/nivo)
    "Pumpa1.Radi", "Pumpa2.Radi", "Rezervoar.Kvar",
    # PLC2 (ventil/pritisak)
    "Ventil.Otvoren", "Cev.Kvar",
]

# Tagovi opasnih vrednosti i njihovi pragovi — za korelaciju "upis + opasno".
# Ovi SE gledaju po vrednosti (ne po promeni), za razliku od IMPORTANT_TAGS.
DANGER_THRESHOLDS = {
    "Cev.Pritisak": 85.0,
    "Rezervoar.Nivo": 95.0,
}


class BasicCorrelator(Correlator):
    # Pravila koja se NE smeju stisavati (realni napadi i bez procesne promene).
    NO_LOWER_RULES = ("RULE-004", "RULE-006", "RULE-008")

    def __init__(self, telemetry_repository: TelemetryRepository, enabled: bool = True):
        self.telemetry_repository = telemetry_repository
        self.enabled = enabled

    def correlate(self, alert: SecurityAlert) -> CorrelationResult:
        if not self.enabled:
            return CorrelationResult(
                score=0,
                final_severity=alert.severity,
                correlated=False,
                details={"correlation_disabled": True},
            )

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

        # NOVA KORELACIJA: neovlascen upis + opasna procesna vrednost = sabotaza.
        # Za RULE-007 (upis) gledamo opasnu vrednost u SIREM prozoru UNAPRED,
        # jer sabotaza (npr. zatvaranje ventila) digne pritisak tek par sekundi
        # kasnije. Za ostala pravila koristimo obican ±W prozor.
        if alert.rule_id == "RULE-007":
            look_end = alert.timestamp + timedelta(seconds=DANGER_LOOKAHEAD_SECONDS)
            danger_telemetry = self.telemetry_repository.get_between(
                alert.timestamp - window, look_end
            )
            danger = self._dangerous_value(danger_telemetry)
            if danger is not None:
                score += 3
                details["write_plus_danger"] = danger  # {tag, value, threshold}
        else:
            danger = self._dangerous_value(telemetry)
            if danger is not None:
                details["dangerous_value"] = danger

        final_severity = self._apply_score(alert.severity, score, alert.rule_id)
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

    def _dangerous_value(self, telemetry: list) -> dict | None:
        """Vrati podatke o prvoj opasnoj vrednosti u prozoru, ili None."""
        for t in telemetry:
            threshold = DANGER_THRESHOLDS.get(t.tag)
            if threshold is None:
                continue
            if t.value >= threshold:
                return {"tag": t.tag, "value": t.value, "threshold": threshold}
        return None

    def _apply_score(self, base: Severity, score: int, rule_id: str) -> Severity:
        if score >= 2:
            return raise_severity(base, score - 1)
        if score == 0 and base == Severity.MEDIUM and rule_id not in self.NO_LOWER_RULES:
            return lower_severity(base, 2)
        return base