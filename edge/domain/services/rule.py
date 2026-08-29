from abc import ABC, abstractmethod

from edge.domain.models.event import Event
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.services.rule_context import RuleContext


class Rule(ABC):
    rule_id: str
    enabled: bool

    @abstractmethod
    def check(self, event: Event, context: RuleContext) -> SecurityAlert | None:
        ...