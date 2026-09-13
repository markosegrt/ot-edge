from datetime import timedelta, datetime

from edge.domain.enums.severity import Severity
from edge.domain.models.security_alert import SecurityAlert
from edge.domain.models.correlation_result import CorrelationResult
from edge.domain.repositories.telemetry_repository import TelemetryRepository
from edge.domain.services.correlator import Correlator
from edge.helpers.severity_scale import raise_severity, lower_severity


WINDOW_SECONDS = 5
DANGER_LOOKAHEAD_SECONDS = 15

IMPORTANT_TAGS = [
    "Pumpa1.Radi", "Pumpa2.Radi", "Rezervoar.Kvar",
    "Ventil.Otvoren", "Cev.Kvar",
]

DANGER_THRESHOLDS = {
    "Cev.Pritisak": 85.0,
    "Rezervoar.Nivo": 95.0,
}

# Analogne vrednosti i koliko promene se smatra "znacajnom" (za RULE-002).
ANALOG_SWING = {
    "Cev.Pritisak": 20.0,
    "Rezervoar.Nivo": 20.0,
}

# Ljudska imena tagova za opise u kartici.
TAG_LABELS = {
    "Cev.Pritisak": "pritisak",
    "Rezervoar.Nivo": "nivo",
    "Pumpa1.Radi": "Pumpa1",
    "Pumpa2.Radi": "Pumpa2",
    "Ventil.Otvoren": "Ventil",
    "Cev.Kvar": "kvar (pritisak)",
    "Rezervoar.Kvar": "kvar (rezervoar)",
}

PATTERN_WRITE_TO_DANGER = "WRITE_TO_DANGER"
PATTERN_UNKNOWN_ACCESS_WITH_CHANGE = "UNKNOWN_ACCESS_WITH_CHANGE"
PATTERN_UNKNOWN_ACCESS_NO_CHANGE = "UNKNOWN_ACCESS_NO_CHANGE"


class BasicCorrelator(Correlator):
    NO_LOWER_RULES = ("RULE-004", "RULE-006", "RULE-008")

    def __init__(self, telemetry_repository: TelemetryRepository, enabled: bool = True):
        self.telemetry_repository = telemetry_repository
        self.enabled = enabled

    def correlate(self, alert: SecurityAlert) -> CorrelationResult:
        if not self.enabled:
            return CorrelationResult(
                score=0,
                final_severity=alert.severity,
                correlated=False,
                details={"correlation_disabled": True},
            )

        window = timedelta(seconds=WINDOW_SECONDS)
        start = alert.timestamp - window
        end = alert.timestamp + window

        telemetry = self.telemetry_repository.get_between(start, end)

        score = 0
        details = {}
        base_severity = alert.severity
        pattern = None
        network_summary = None
        process_summary = None
        link_summary = None

        if self._has_important_change(telemetry):
            score += 2
            details["process_change"] = True

        if alert.rule_id in ("RULE-002", "RULE-007"):
            score += 1
            details["critical_rule"] = alert.rule_id

        # OBRAZAC 1: neovlascen upis + opasna procesna vrednost = sabotaza.
        if alert.rule_id == "RULE-007":
            look_end = alert.timestamp + timedelta(seconds=DANGER_LOOKAHEAD_SECONDS)
            danger_telemetry = self.telemetry_repository.get_between(
                alert.timestamp - window, look_end
            )
            danger = self._dangerous_value(danger_telemetry)
            if danger is not None:
                score += 3
                details["write_plus_danger"] = danger

                pattern = PATTERN_WRITE_TO_DANGER
                label = TAG_LABELS.get(danger["tag"], danger["tag"])
                network_summary = (
                    f"Neovlašćen upis: {alert.source} → {alert.destination}. "
                    f"Izvor nije ovlašćen za upis u PLC (zaobišao SCADA lanac)."
                )
                process_summary = (
                    f"U procesu je {label} dostigao {danger['value']:.0f} "
                    f"(prag {danger['threshold']:.0f}) u roku od "
                    f"{DANGER_LOOKAHEAD_SECONDS}s posle upisa."
                )
                link_summary = (
                    f"Upis i opasna vrednost poklopili su se u vremenu — "
                    f"upis je uzrok, skok vrednosti ({label}) je posledica. "
                    f"Mreža sama ovo ne vidi kao kritično."
                )

        # OBRAZAC 2: nepoznat pristup PLC-u koji se poklapa sa promenom procesa.
        # Gledamo CEO raspon toka. "Promena" = prekidacki tag (Ventil/pumpe/kvar)
        # ILI znacajan porast analogne vrednosti (pritisak/nivo).
        elif alert.rule_id == "RULE-002":
            first_raw = alert.extra.get("flow_first_seen")
            last_raw = alert.extra.get("flow_last_seen")
            if first_raw and last_raw:
                flow_start = datetime.fromisoformat(first_raw) - window
                flow_end = datetime.fromisoformat(last_raw) + window
                flow_telemetry = self.telemetry_repository.get_between(flow_start, flow_end)
            else:
                flow_telemetry = telemetry

            changed = self._changed_important_tags(flow_telemetry)
            swing = self._significant_swing(flow_telemetry)

            if changed or swing is not None:
                pattern = PATTERN_UNKNOWN_ACCESS_WITH_CHANGE

                if changed:
                    proc_desc = ", ".join(TAG_LABELS.get(t, t) for t in changed)
                else:
                    slabel = TAG_LABELS.get(swing["tag"], swing["tag"])
                    proc_desc = (
                        f"{slabel} se promenio sa {swing['min']:.0f} na "
                        f"{swing['max']:.0f}"
                    )

                network_summary = (
                    f"Nepoznat/neovlašćen uređaj {alert.source} komunicira sa "
                    f"PLC-om {alert.destination} (nije u listi poznatih uređaja)."
                )
                process_summary = (
                    f"Tokom komunikacije zabeležena je promena procesa: {proc_desc}."
                )
                link_summary = (
                    f"Pristup nepoznatog uređaja poklopio se sa promenom procesa. "
                    f"Nepoznat uređaj koji samo posmatra nije sumnjiv — ali onaj "
                    f"koji priča sa PLC-om baš dok se proces menja jeste."
                )
                if not details.get("process_change"):
                    score += 2
                    details["process_change"] = True
            else:
                # Nepoznat pristup PLC-u BEZ procesne promene. Sumnjivo, ali bez
                # potvrdjene fizicke posledice -> ostaje HIGH (ne dizemo score).
                # Ipak dobija opis, da kartica nije prazna i da se vidi RAZLIKA
                # naspram slucaja sa promenom (koji ide na CRITICAL).
                pattern = PATTERN_UNKNOWN_ACCESS_NO_CHANGE
                network_summary = (
                    f"Nepoznat/neovlašćen uređaj {alert.source} komunicira sa "
                    f"PLC-om {alert.destination} (nije u listi poznatih uređaja)."
                )
                process_summary = (
                    f"U posmatranom periodu proces se NIJE menjao — pristup "
                    f"nije praćen procesnom posledicom."
                )
                link_summary = (
                    f"Nepoznat uređaj priča sa PLC-om, ali proces miruje. To liči "
                    f"na izviđanje/osmatranje, ne na aktivnu sabotažu. Zato ostaje "
                    f"{base_severity.value} — sumnjivo, ali bez potvrđenog fizičkog "
                    f"uticaja."
                )

        else:
            danger = self._dangerous_value(telemetry)
            if danger is not None:
                details["dangerous_value"] = danger

        final_severity = self._apply_score(alert.severity, score, alert.rule_id)
        correlated = score > 0

        return CorrelationResult(
            score=score,
            final_severity=final_severity,
            correlated=correlated,
            details=details,
            pattern=pattern,
            base_severity=base_severity,
            network_summary=network_summary,
            process_summary=process_summary,
            link_summary=link_summary,
        )

    def _has_important_change(self, telemetry: list) -> bool:
        by_tag = {}
        for t in telemetry:
            if t.tag not in IMPORTANT_TAGS:
                continue
            by_tag.setdefault(t.tag, set()).add(t.value)

        for tag, values in by_tag.items():
            if len(values) > 1:
                return True
        return False

    def _changed_important_tags(self, telemetry: list) -> list[str]:
        by_tag = {}
        for t in telemetry:
            if t.tag not in IMPORTANT_TAGS:
                continue
            by_tag.setdefault(t.tag, set()).add(t.value)
        return [tag for tag, values in by_tag.items() if len(values) > 1]

    def _significant_swing(self, telemetry: list) -> dict | None:
        """Vrati analognu vrednost koja se znacajno promenila u rasponu, ili None."""
        by_tag = {}
        for t in telemetry:
            if t.tag not in ANALOG_SWING:
                continue
            by_tag.setdefault(t.tag, []).append(t.value)

        for tag, values in by_tag.items():
            if not values:
                continue
            lo, hi = min(values), max(values)
            if hi - lo >= ANALOG_SWING[tag]:
                return {"tag": tag, "min": lo, "max": hi}
        return None

    def _dangerous_value(self, telemetry: list) -> dict | None:
        for t in telemetry:
            threshold = DANGER_THRESHOLDS.get(t.tag)
            if threshold is None:
                continue
            if t.value >= threshold:
                return {"tag": t.tag, "value": t.value, "threshold": threshold}
        return None

    def _apply_score(self, base: Severity, score: int, rule_id: str) -> Severity:
        if score >= 2:
            return raise_severity(base, score - 1)
        if score == 0 and base == Severity.MEDIUM and rule_id not in self.NO_LOWER_RULES:
            return lower_severity(base, 2)
        return base