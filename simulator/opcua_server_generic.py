"""
opcua_server_generic.py — GENERICKI OPC UA IZLOG

Radi sa bilo kojim mozgom koji ispunjava interfejs ProcessDevice.
Mozak kaze kako izgleda njegovo OPC UA stablo (opcua_structure) i koje
su trenutne vrednosti (opcua_values). Server gradi stablo i osvezava ga.
"""

import asyncio
import os

from asyncua import Server


NAMESPACE_URI = "http://otedge.local/plant-sim"


class GenericOpcUaServer:
    def __init__(self, device, namespace_uri: str = NAMESPACE_URI):
        self.device = device
        self.namespace_uri = namespace_uri
        self.server = Server()
        self.nodes = {}  # {(objekat, varijabla): node}

    async def setup(self):
        await self.server.init()

        port = int(os.environ.get("OPCUA_PORT", "4840"))
        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{port}/otedge/")
        self.server.set_server_name("OT Edge Plant Simulator")

        idx = await self.server.register_namespace(self.namespace_uri)
        objects = self.server.nodes.objects
        root = await objects.add_object(idx, "Postrojenje")

        # Napravi stablo iz opisa koji je dao mozak
        structure = self.device.opcua_structure()
        for obj_name, variables in structure.items():
            obj = await root.add_object(idx, obj_name)
            for var_name, init_val in variables:
                node = await obj.add_variable(idx, var_name, init_val)
                await node.set_writable(False)
                self.nodes[(obj_name, var_name)] = node

        port = int(os.environ.get("OPCUA_PORT", "4840"))
        print(f"OPC UA server podesen na opc.tcp://0.0.0.0:{port}/otedge/", flush=True)

    async def refresh_values(self):
        values = self.device.opcua_values()
        for obj_name, vars_dict in values.items():
            for var_name, val in vars_dict.items():
                node = self.nodes.get((obj_name, var_name))
                if node is not None:
                    await node.write_value(val)

    async def run_server(self):
        await self.setup()
        async with self.server:
            print("OPC UA server: radi.", flush=True)
            while True:
                await self.refresh_values()
                await asyncio.sleep(0.1)