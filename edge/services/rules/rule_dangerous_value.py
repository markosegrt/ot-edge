from datetime import datetime, timezone, timedelta

from edge.domain.enums.event_type import EventType
from edge.domain.enums.protocol import Protocol
from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


# Podrazumevani pragovi ako nisu zadati u rules.yaml (params).
DEFAULT_THRESHOLDS = {
    "Cev.Pritisak": 85.0,      # bar — opasno visok pritisak
    "Rezervoar.Nivo": 95.0,    # % — skoro prepun
}
LOOKBACK_SECONDS = 5


class DangerousValueRule(Rule):
    """
    RULE-008: procesna vrednost presla opasan prag.

    Za razliku od mreznih pravila, ovo gleda PROCES: cita skorasnju telemetriju
    i okida ako je neka vazna vrednost (pritisak, nivo) presla prag.

    Sam po sebi je nizeg znacaja (npr. moze biti i legitiman kvar), ali kad se
    korelira sa neovlascenim upisom (RULE-007) u istom prozoru -> CRITICAL.
    To je scenario napada: neko zatvori ventil, pritisak skoci do opasnog.
    """

    def __init__(self, config: RuleConfig, telemetry_repository: TelemetryRepository):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity
        self.thresholds = config.params.get("thresholds", DEFAULT_THRESHOLDS)
        self.telemetry_repository = telemetry_repository

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        # Vreme DOGADJAJA, ne "sada" — u measurement modu su podaci iz proslosti.
        end = event.timestamp
        start = end - timedelta(seconds=LOOKBACK_SECONDS)
        telemetry = self.telemetry_repository.get_between(start, end)

        for t in telemetry:
            threshold = self.thresholds.get(t.tag)
            if threshold is None:
                continue
            if t.value >= threshold:
                return SecurityAlert(
                    timestamp=t.timestamp,
                    rule_id=self.rule_id,
                    severity=self.severity,
                    event_type=EventType.PROCESS,
                    source=t.device_ip or t.device,
                    destination=t.device_ip or t.device,
                    device=t.device,
                    protocol=Protocol.OPCUA,
                    extra={
                        "reason": "dangerous_process_value",
                        "tag": t.tag,
                        "value": t.value,
                        "threshold": threshold,
                    },
                )
        return None