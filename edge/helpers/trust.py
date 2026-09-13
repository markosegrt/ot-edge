from edge.domain.models.baseline_device import BaselineDevice


def is_suspicious(baseline_by_ip: dict[str, BaselineDevice], ip: str) -> bool:
    """Sumnjiv ako nije u baseline-u, ili jeste ali netrust."""
    known = baseline_by_ip.get(ip)
    if known is None:
        return True
    return not known.trusted