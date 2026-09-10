"""
scada_proxy.py — SCADA AS THE MIDDLE OF THE CHAIN (HMI -> SCADA -> PLC)

SCADA is no longer a plain client. It is the middle of the Purdue chain:

  - CLIENT to both PLCs (.10 pumps/level, .11 valve/pressure):
    continuously reads their state. Two INDEPENDENT clients (one task per PLC),
    so one PLC failing does not stall reading the other.

  - SERVER ("process image") to the HMI: the HMI reads the combined state of
    both PLCs from SCADA, and sends ALL commands to SCADA. SCADA FORWARDS them
    to the real PLC.

The "process image" is the standard OT term: SCADA holds a live picture of the
whole plant's process state and exposes it to the supervisory layer (HMI).

Why: the only legitimate write path into a PLC is THROUGH SCADA. The HMI never
talks to a PLC directly. An attacker writing straight to a PLC BYPASSES the
chain — and that is exactly what RULE-007 catches (the only device allowed to
write to a PLC is SCADA .30).

Everything stays on Modbus — no other protocol is introduced.

Commands are ABSOLUTE (target state 1=ON / 0=OFF), never toggles. This avoids
the ping-pong problem: the HMI says "pump1 = ON", not "flip pump1".

Run:
    PLC1_HOST=192.168.10.10 PLC2_HOST=192.168.10.11 \
    IMAGE_PORT=502 python3 -m clients.scada_proxy
"""

import asyncio
import os

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer


# ---------- PROCESS IMAGE MAP ----------
# The HMI sees both PLCs through one set of registers/coils on SCADA.
# The gap (PLC1 at 0-2, PLC2 at 10+) leaves room to add a third PLC later.

# Holding registers in the process image
IMG_REG_PLC1_LEVEL = 0        # level * 10
IMG_REG_PLC1_P1SPEED = 1
IMG_REG_PLC1_P2SPEED = 2
IMG_REG_PLC2_PRESSURE = 10    # pressure * 10

# Coils in the process image
IMG_COIL_PLC1_PUMP1 = 0       # command + state
IMG_COIL_PLC1_PUMP2 = 1       # command + state
IMG_COIL_PLC1_FAULT = 2       # state only
IMG_COIL_PLC2_VALVE = 10      # command + state
IMG_COIL_PLC2_FAULT = 11      # state only

# How many coils/registers SCADA reads from each PLC (how much they expose)
PLC1_NUM_COILS = 3    # pump1, pump2, fault
PLC1_NUM_REG = 3      # level, p1_speed, p2_speed
PLC2_NUM_COILS = 2    # valve, fault
PLC2_NUM_REG = 1      # pressure

READ_INTERVAL = 1.0       # SCADA refreshes the process image every second
COMMAND_INTERVAL = 0.3    # how often it checks for HMI writes to forward


class ScadaProxy:
    def __init__(self, plc1_host: str, plc2_host: str, plc_port: int):
        self.plc1_host = plc1_host
        self.plc2_host = plc2_host
        self.plc_port = plc_port

        # The process image the HMI reads. Same shape as a real PLC store.
        self.store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [0] * 100),
            hr=ModbusSequentialDataBlock(0, [0] * 100),
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)

        # Clients to the PLCs (created in run())
        self.plc1_client: AsyncModbusTcpClient | None = None
        self.plc2_client: AsyncModbusTcpClient | None = None

        # Last known ACTUAL PLC command-coil state. We forward an HMI write only
        # when the image differs from the real PLC — so we push CHANGES, not the
        # same value over and over. None = "not read yet".
        self._plc1_pump1: int | None = None
        self._plc1_pump2: int | None = None
        self._plc2_valve: int | None = None

    # ---------- CLIENT: read PLC1 (pumps/level) ----------

    async def read_plc1(self):
        """Continuously read PLC1 and fill its part of the process image."""
        while True:
            try:
                if self.plc1_client is None or not self.plc1_client.connected:
                    self.plc1_client = AsyncModbusTcpClient(
                        self.plc1_host, port=self.plc_port
                    )
                    await self.plc1_client.connect()

                rr = await self.plc1_client.read_holding_registers(
                    address=0, count=PLC1_NUM_REG
                )
                rc = await self.plc1_client.read_coils(
                    address=0, count=PLC1_NUM_COILS
                )

                if not rr.isError() and not rc.isError():
                    # Registers PLC1 -> image 0..2
                    self.store.setValues(3, IMG_REG_PLC1_LEVEL, [rr.registers[0]])
                    self.store.setValues(3, IMG_REG_PLC1_P1SPEED, [rr.registers[1]])
                    self.store.setValues(3, IMG_REG_PLC1_P2SPEED, [rr.registers[2]])
                    # Fault -> image
                    self.store.setValues(1, IMG_COIL_PLC1_FAULT, [int(rc.bits[2])])

                    # Track the real command-coil state so the HMI sees the
                    # truth on startup, and so we know what "changed" means.
                    real_p1 = int(rc.bits[0])
                    real_p2 = int(rc.bits[1])
                    if self._plc1_pump1 is None:
                        self._plc1_pump1 = real_p1
                        self.store.setValues(1, IMG_COIL_PLC1_PUMP1, [real_p1])
                    if self._plc1_pump2 is None:
                        self._plc1_pump2 = real_p2
                        self.store.setValues(1, IMG_COIL_PLC1_PUMP2, [real_p2])
            except Exception as e:
                print(f"[SCADA] PLC1 ({self.plc1_host}) error: {e}", flush=True)
                self.plc1_client = None

            await asyncio.sleep(READ_INTERVAL)

    # ---------- CLIENT: read PLC2 (valve/pressure) ----------

    async def read_plc2(self):
        """Continuously read PLC2 and fill its part of the image. Independent of PLC1."""
        while True:
            try:
                if self.plc2_client is None or not self.plc2_client.connected:
                    self.plc2_client = AsyncModbusTcpClient(
                        self.plc2_host, port=self.plc_port
                    )
                    await self.plc2_client.connect()

                rr = await self.plc2_client.read_holding_registers(
                    address=0, count=PLC2_NUM_REG
                )
                rc = await self.plc2_client.read_coils(
                    address=0, count=PLC2_NUM_COILS
                )

                if not rr.isError() and not rc.isError():
                    # Register PLC2 -> image 10
                    self.store.setValues(3, IMG_REG_PLC2_PRESSURE, [rr.registers[0]])
                    self.store.setValues(1, IMG_COIL_PLC2_FAULT, [int(rc.bits[1])])

                    real_valve = int(rc.bits[0])
                    if self._plc2_valve is None:
                        self._plc2_valve = real_valve
                        self.store.setValues(1, IMG_COIL_PLC2_VALVE, [real_valve])
            except Exception as e:
                print(f"[SCADA] PLC2 ({self.plc2_host}) error: {e}", flush=True)
                self.plc2_client = None

            await asyncio.sleep(READ_INTERVAL)

    # ---------- FORWARD COMMANDS: process image -> real PLC ----------

    async def forward_commands(self):
        """
        Check whether the HMI wrote a new target into the process image. If the
        image differs from the real PLC command state, SCADA forwards that exact
        value to the PLC. Absolute target (1/0), not a toggle — no ping-pong.
        This is the only legitimate write path into a PLC.
        """
        while True:
            try:
                # --- PLC1 pumps ---
                if self.plc1_client and self.plc1_client.connected and self._plc1_pump1 is not None:
                    img_p1 = self.store.getValues(1, IMG_COIL_PLC1_PUMP1, count=1)[0]
                    img_p2 = self.store.getValues(1, IMG_COIL_PLC1_PUMP2, count=1)[0]

                    if img_p1 != self._plc1_pump1:
                        await self.plc1_client.write_coil(0, bool(img_p1))
                        print(f"[SCADA] command -> PLC1 Pump1 = {'ON' if img_p1 else 'OFF'}", flush=True)
                        self._plc1_pump1 = img_p1
                    if img_p2 != self._plc1_pump2:
                        await self.plc1_client.write_coil(1, bool(img_p2))
                        print(f"[SCADA] command -> PLC1 Pump2 = {'ON' if img_p2 else 'OFF'}", flush=True)
                        self._plc1_pump2 = img_p2

                # --- PLC2 valve ---
                if self.plc2_client and self.plc2_client.connected and self._plc2_valve is not None:
                    img_v = self.store.getValues(1, IMG_COIL_PLC2_VALVE, count=1)[0]
                    if img_v != self._plc2_valve:
                        await self.plc2_client.write_coil(0, bool(img_v))
                        print(f"[SCADA] command -> PLC2 Valve = {'OPEN' if img_v else 'CLOSED'}", flush=True)
                        self._plc2_valve = img_v
            except Exception as e:
                print(f"[SCADA] error forwarding command: {e}", flush=True)

            await asyncio.sleep(COMMAND_INTERVAL)

    # ---------- SERVER: process image to the HMI ----------

    async def run_server(self):
        port = int(os.environ.get("IMAGE_PORT", "502"))
        print(f"[SCADA] process image (Modbus server) listening on port {port}", flush=True)
        await StartAsyncTcpServer(context=self.context, address=("0.0.0.0", port))

    # ---------- All together ----------

    async def run(self):
        print(f"[SCADA] start: client to PLC1={self.plc1_host}, "
              f"PLC2={self.plc2_host}; process image for HMI", flush=True)
        await asyncio.gather(
            self.run_server(),
            self.read_plc1(),
            self.read_plc2(),
            self.forward_commands(),
        )


async def main():
    plc1_host = os.environ.get("PLC1_HOST", "192.168.10.10")
    plc2_host = os.environ.get("PLC2_HOST", "192.168.10.11")
    plc_port = int(os.environ.get("PLC_PORT", "502"))

    proxy = ScadaProxy(plc1_host, plc2_host, plc_port)
    await proxy.run()


if __name__ == "__main__":
    asyncio.run(main())