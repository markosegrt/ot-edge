from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


DEFAULT_PACKET_THRESHOLD = 300


class FloodRule(Rule):
    """
    RULE-004: volumetrijski napad (flood).

    Okida kad neki izvor ima tok sa neuobicajeno velikim brojem paketa —
    znak rafalnog saobracaja (npr. napadac baca Modbus zahteve u petlji).

    Normalan HMI/SCADA saobracaj ima desetine paketa po toku; flood ima
    stotine/hiljade. Prag (packet_threshold) stoji izmedju te dve velicine,
    pa normalan rad ne okida lazno. Podesiv je iz rules.yaml.
    """

    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity
        self.packet_threshold = config.params.get(
            "packet_threshold", DEFAULT_PACKET_THRESHOLD
        )

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        max_packets = context.max_packets_by_source.get(event.source, 0)
        if max_packets < self.packet_threshold:
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
                "reason": "packet_flood",
                "source_ip": event.source,
                "packet_count": max_packets,
                "threshold": self.packet_threshold,
            },
        )