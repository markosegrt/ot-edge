from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext
from edge.helpers.trust import is_suspicious


PORT_SCAN_THRESHOLD = 10


class PortScanRule(Rule):
    """
    RULE-006: skeniranje portova.

    Okida kad SUMNJIV izvor (nepoznat ili netrust) kontaktira mnogo RAZLICITIH
    portova (izvidjanje). Pouzdani uredjaji (PLC, SCADA) ne skeniraju — pa ne
    mogu biti izvor. Broj RAZLICITIH portova (ne paketa) razdvaja scan od flood-a:
    flood ide na jedan port (mnogo paketa), scan na mnogo portova.
    """

    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        # Scan dolazi samo od sumnjivog izvora. PLC/SCADA ne skeniraju.
        if not is_suspicious(context.baseline_by_ip, event.source):
            return None

        ports = context.ports_by_source.get(event.source, set())
        if len(ports) < PORT_SCAN_THRESHOLD:
            return None

        return SecurityAlert(
            timestamp=event.timestamp,
            rule_id=self.rule_id,
            severity=self.severity,
            event_type=event.event_type,
            source=event.source,
            destination=event.destination,
            device=event.device,
            protocol=event.protocol,
            extra={
                "reason": "port_scan",
                "source_ip": event.source,
                "port_count": len(ports),
            },
        )