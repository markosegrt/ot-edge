from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext
from edge.helpers.trust import is_suspicious


DEFAULT_PACKET_THRESHOLD = 300


class FloodRule(Rule):
    """
    RULE-004: volumetrijski napad (flood).

    Okida kad SUMNJIV izvor (nepoznat ili netrust) ima tok sa neuobicajeno
    velikim brojem paketa. Pouzdani uredjaji (PLC, SCADA) NE mogu biti izvor
    flood-a — inace bi PLC koji odgovara na flood lazno okidao pravilo.

    Prag (packet_threshold) podesiv iz rules.yaml.
    """

    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity
        self.packet_threshold = config.params.get(
            "packet_threshold", DEFAULT_PACKET_THRESHOLD
        )

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        # Flood dolazi samo od sumnjivog izvora. PLC/SCADA ne floduju.
        if not is_suspicious(context.baseline_by_ip, event.source):
            return None

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