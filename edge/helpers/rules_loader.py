import yaml

from edge.domain.enums.severity import Severity
from edge.domain.models.rule_config import RuleConfig


def load_rules(path: str) -> dict[str, RuleConfig]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    result = {}
    for entry in data:
        config = RuleConfig(
            rule_id=entry["id"],
            name=entry["name"],
            enabled=entry.get("enabled", True),
            severity=Severity(entry["severity"]),
        )
        result[config.rule_id] = config
    return result