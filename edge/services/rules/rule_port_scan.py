from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


PORT_SCAN_THRESHOLD = 10


class PortScanRule(Rule):
    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
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