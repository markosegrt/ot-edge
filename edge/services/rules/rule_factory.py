from edge.domain.models.rule_config import RuleConfig
from edge.domain.services.rule import Rule
from edge.services.rules.rule_new_device import NewDeviceRule
from edge.services.rules.rule_unknown_to_plc import UnknownToPlcRule

RULE_CLASSES = {
    "RULE-001": NewDeviceRule,
    "RULE-002": UnknownToPlcRule,
}


def build_rules(configs: dict[str, RuleConfig]) -> list[Rule]:
    rules = []
    for rule_id, rule_class in RULE_CLASSES.items():
        config = configs.get(rule_id)
        if config is None:
            continue
        rules.append(rule_class(config))
    return rules