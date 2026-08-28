# edge/config/settings.py
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_USER: str = os.getenv("DB_USER", "otedge")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "otedge")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "otedge")

    OPCUA_HOST: str = os.getenv("OPCUA_HOST", "192.168.10.11")
    OPCUA_PORT: str = os.getenv("OPCUA_PORT", "4840")
    OPCUA_PATH: str = os.getenv("OPCUA_PATH", "/otedge/")

    PCAP_PATH: str = os.getenv("PCAP_PATH", "tests/pcaps/lab_normal.pcap")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def opcua_url(self) -> str:
        return f"opc.tcp://{self.OPCUA_HOST}:{self.OPCUA_PORT}{self.OPCUA_PATH}"

    @property
    def pcap_path(self) -> str:
        return self.PCAP_PATH

settings = Settings()