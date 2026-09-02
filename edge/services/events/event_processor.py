from datetime import datetime, timezone

from edge.domain.enums.device_type import DeviceType
from edge.domain.enums.event_type import EventType
from edge.domain.enums.protocol import Protocol
from edge.domain.enums.severity import Severity
from edge.domain.models.baseline_device import BaselineDevice
from edge.domain.models.device import Device
from edge.domain.models.flow import Flow
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.repositories.device_repository import DeviceRepository
from edge.domain.repositories.security_event_repository import SecurityEventRepository
from edge.domain.services.event_processor import EventProcessor
from edge.domain.services.normalizer import Normalizer
from edge.domain.services.correlator import Correlator
from edge.domain.services.rule_context import RuleContext
from edge.services.rules.rule_engine import RuleEngine
from edge.domain.repositories.flow_repository import FlowRepository

class BasicEventProcessor(EventProcessor):
    def __init__(
        self,
        normalizer: Normalizer,
        engine: RuleEngine,
        correlator: Correlator,
        device_repository: DeviceRepository,
        flow_repository: FlowRepository,
        alert_repository: SecurityEventRepository,
        baseline: dict[str, BaselineDevice],
    ):
        self.normalizer = normalizer
        self.engine = engine
        self.correlator = correlator
        self.device_repository = device_repository
        self.flow_repository = flow_repository
        self.alert_repository = alert_repository
        self.baseline = baseline

    def process_flow(self, flow: Flow) -> None:
        event = self.normalizer.from_flow(flow)
        self._evaluate_and_store(event)

    def process_modbus_write(self, write_data: dict) -> None:
        event = self.normalizer.from_modbus_write(
            src_ip=write_data["src_ip"],
            dst_ip=write_data["dst_ip"],
            src_port=write_data["src_port"],
            dst_port=write_data["dst_port"],
            function_code=write_data["function_code"],
            start_address=write_data["start_address"],
            timestamp=write_data["timestamp"],
        )
        self._evaluate_and_store(event)

    def process_unavailable_device(self, device: Device) -> None:
        severity = Severity.HIGH if device.device_type == DeviceType.PLC else Severity.MEDIUM

        alert = SecurityAlert(
            timestamp=datetime.now(timezone.utc),
            rule_id="RULE-003",
            severity=severity,
            event_type=EventType.NETWORK,
            source=device.ip,
            destination=device.ip,
            device=device.ip,
            protocol=Protocol.OTHER,
            extra={"reason": "device_unavailable", "device_type": device.device_type.value},
        )
        self.alert_repository.save(alert)

    def _evaluate_and_store(self, event) -> None:
        from datetime import timedelta

        context = self._build_context()
        alerts = self.engine.evaluate(event, context)
        for alert in alerts:
            result = self.correlator.correlate(alert)
            alert.severity = result.final_severity
            alert.correlated = result.correlated
            alert.extra["correlation"] = result.details
            self._store_with_dedup(alert)

    def _build_context(self) -> RuleContext:
        devices = self.device_repository.get_all()
        devices_by_ip = {d.ip: d for d in devices}

        ports_by_source = {}
        flows = self.flow_repository.get_all()
        for flow in flows:
            ports_by_source.setdefault(flow.source_ip, set()).add(flow.destination_port)

        return RuleContext(
            devices_by_ip=devices_by_ip,
            baseline_by_ip=self.baseline,
            ports_by_source=ports_by_source,
        )

    def _store_with_dedup(self, alert) -> None:
        from datetime import timedelta

        window_start = alert.timestamp - timedelta(seconds=60)
        duplicate_id = self.alert_repository.find_recent_duplicate_id(
            rule_id=alert.rule_id,
            source=alert.source,
            destination=alert.destination,
            since=window_start,
        )
        if duplicate_id is not None:
            self.alert_repository.increment_occurrence(duplicate_id)
        else:
            self.alert_repository.save(alert)