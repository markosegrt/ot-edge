# edge/services/events/event_processor.py
from edge.domain.models.baseline_device import BaselineDevice
from edge.domain.models.flow import Flow
from edge.domain.repositories.device_repository import DeviceRepository
from edge.domain.repositories.security_event_repository import SecurityEventRepository
from edge.domain.services.event_processor import EventProcessor
from edge.domain.services.normalizer import Normalizer
from edge.domain.services.rule_context import RuleContext
from edge.services.rules.rule_engine import RuleEngine


class BasicEventProcessor(EventProcessor):
    def __init__(
        self,
        normalizer: Normalizer,
        engine: RuleEngine,
        device_repository: DeviceRepository,
        alert_repository: SecurityEventRepository,
        baseline: dict[str, BaselineDevice],
    ):
        self.normalizer = normalizer
        self.engine = engine
        self.device_repository = device_repository
        self.alert_repository = alert_repository
        self.baseline = baseline

    def process_flow(self, flow: Flow) -> None:
        event = self.normalizer.from_flow(flow)
        context = self._build_context()
        alerts = self.engine.evaluate(event, context)
        for alert in alerts:
            self.alert_repository.save(alert)

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
        context = self._build_context()
        alerts = self.engine.evaluate(event, context)
        for alert in alerts:
            self.alert_repository.save(alert)

    def _build_context(self) -> RuleContext:
        devices = self.device_repository.get_all()
        devices_by_ip = {d.ip: d for d in devices}
        return RuleContext(devices_by_ip=devices_by_ip, baseline_by_ip=self.baseline)