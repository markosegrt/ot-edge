from edge.domain.enums.device_status import DeviceStatus
from edge.domain.enums.device_type import DeviceType
from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


class UnknownToPlcRule(Rule):
    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        source_device = context.devices_by_ip.get(event.source)
        destination_device = context.devices_by_ip.get(event.destination)

        if destination_device is None or destination_device.device_type != DeviceType.PLC:
            return None

        source_is_suspicious = (
            source_device is None
            or source_device.status in (DeviceStatus.NEW, DeviceStatus.UNAVAILABLE)
        )
        if not source_is_suspicious:
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
            extra={"reason": "unknown_device_to_plc", "source_ip": event.source},
        )