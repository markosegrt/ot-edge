from edge.domain.enums.severity import Severity


SEVERITY_ORDER = [
    Severity.INFO,
    Severity.LOW,
    Severity.MEDIUM,
    Severity.HIGH,
    Severity.CRITICAL,
]


def raise_severity(base: Severity, steps: int) -> Severity:
    index = SEVERITY_ORDER.index(base)
    new_index = min(index + steps, len(SEVERITY_ORDER) - 1)
    return SEVERITY_ORDER[new_index]


def lower_severity(base: Severity, steps: int) -> Severity:
    index = SEVERITY_ORDER.index(base)
    new_index = max(index - steps, 0)
    return SEVERITY_ORDER[new_index]