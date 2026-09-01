from abc import ABC, abstractmethod

from edge.domain.models.security_alert import SecurityAlert
from edge.domain.models.correlation_result import CorrelationResult


class Correlator(ABC):
    @abstractmethod
    def correlate(self, alert: SecurityAlert) -> CorrelationResult:
        ...