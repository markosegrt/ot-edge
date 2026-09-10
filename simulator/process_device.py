"""
process_device.py — SHARED INTERFACE FOR EVERY PLC

Each brain (first PLC pumps/level, second PLC valve/pressure) fulfills this
contract. Because of it, one Modbus server and one OPC UA server work with ANY
brain — they don't know whether it's pumps or pressure.

The brain "describes itself":
- what it exposes on Modbus (coils = 0/1 values, registers = numbers)
- how it receives Modbus writes (coil -> command)
- what its OPC UA structure looks like (objects -> variables)
- what the current OPC UA values are

A new PLC is added by writing a new brain with these methods — the servers are
NOT touched. That is the point of this interface.
"""

from typing import Protocol, Any


class ProcessDevice(Protocol):
    """Contract every PLC brain must fulfill."""

    def step(self, dt: float | None = None) -> None:
        """Advance the process forward in time."""
        ...

    def render(self) -> str:
        """Short text view of state (for logs)."""
        ...

    # ---------- MODBUS ----------

    def coil_outputs(self) -> list[int]:
        """
        Values that go to Modbus coils, in address order (0, 1, 2, ...).
        Each is 0 or 1. E.g. first PLC: [pump1_running, pump2_running, fault].
        """
        ...

    def register_outputs(self) -> list[int]:
        """
        Values that go to Modbus holding registers, in address order.
        Integers. E.g. first PLC: [level*10, pump1_speed, pump2_speed].
        """
        ...

    def apply_coils(self, coils: list[int]) -> None:
        """
        Apply Modbus writes back onto process state.
        Receives current coil values; the brain decides what they mean.
        E.g. first PLC: coil[0]=1 -> start pump1.
        """
        ...

    # ---------- OPC UA ----------

    def opcua_structure(self) -> dict[str, list[tuple[str, Any]]]:
        """
        OPC UA tree description: {object_name: [(variable_name, initial_value), ...]}.
        E.g. first PLC:
          {
            "Pumpa1": [("Radi", False), ("Brzina", 0.0)],
            "Pumpa2": [("Radi", False), ("Brzina", 0.0)],
            "Rezervoar": [("Nivo", 0.0), ("Kvar", False)],
          }
        """
        ...

    def opcua_values(self) -> dict[str, dict[str, Any]]:
        """
        Current OPC UA values: {object_name: {variable_name: value}}.
        Same shape as opcua_structure, but with live values.
        """
        ...