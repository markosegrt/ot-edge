from edge.domain.models.event import Event
from edge.domain.models.rule_config import RuleConfig
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


class UnauthorizedWriteRule(Rule):
    def __init__(self, config: RuleConfig):
        self.rule_id = config.rule_id
        self.enabled = config.enabled
        self.severity = config.severity

    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        if not event.extra.get("modbus_write"):
            return None

        baseline = context.baseline_by_ip.get(event.source)
        source_may_write = baseline is not None and baseline.can_write
        if source_may_write:
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
                "reason": "unauthorized_modbus_write",
                "function_code": event.extra.get("function_code"),
                "start_address": event.extra.get("start_address"),
                "source_ip": event.source,
            },
        )