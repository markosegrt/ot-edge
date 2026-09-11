from edge.domain.models.rule_config import RuleConfig
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.rule import Rule
from edge.services.rules.rule_new_device import NewDeviceRule
from edge.services.rules.rule_unknown_to_plc import UnknownToPlcRule
from edge.services.rules.rule_unauthorized_write import UnauthorizedWriteRule
from edge.services.rules.rule_port_scan import PortScanRule
from edge.services.rules.rule_flood import FloodRule
from edge.services.rules.rule_dangerous_value import DangerousValueRule

SIMPLE_RULE_CLASSES = {
    "RULE-001": NewDeviceRule,
    "RULE-002": UnknownToPlcRule,
    "RULE-004": FloodRule,
    "RULE-006": PortScanRule,
    "RULE-007": UnauthorizedWriteRule,
}


def build_rules(
    configs: dict[str, RuleConfig],
    telemetry_repository: TelemetryRepository,
) -> list[Rule]:
    rules = []
    for rule_id, rule_class in SIMPLE_RULE_CLASSES.items():
        config = configs.get(rule_id)
        if config is None:
            continue
        rules.append(rule_class(config))

    config_008 = configs.get("RULE-008")
    if config_008 is not None:
        rules.append(DangerousValueRule(config_008, telemetry_repository))

    return rules