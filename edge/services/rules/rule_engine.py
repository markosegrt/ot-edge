from edge.domain.models.event import Event
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule import Rule
from edge.domain.services.rule_context import RuleContext


class RuleEngine:
    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(self, event: Event, context: RuleContext) -> list[SecurityAlert]:
        alerts = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            alert = rule.check(event, context)
            if alert is not None:
                alerts.append(alert)
        return alerts