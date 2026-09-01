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
    BASELINE_PATH: str = os.getenv("BASELINE_PATH", "baseline.yaml")
    RULES_PATH: str = os.getenv("RULES_PATH", "rules.yaml")

    UNAVAILABLE_THRESHOLD_SECONDS: int = int(os.getenv("UNAVAILABLE_THRESHOLD_SECONDS", "30"))

    NETWORK_SOURCE: str = os.getenv("NETWORK_SOURCE", "pcap")

    TELEMETRY_PATH: str = os.getenv("TELEMETRY_PATH", "tests/telemetry/pair_telemetry.jsonl")
    PROCESS_SOURCE: str = os.getenv("PROCESS_SOURCE", "live")

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

    @property
    def baseline_path(self) -> str:
        return self.BASELINE_PATH

    @property
    def rules_path(self) -> str:
        return self.RULES_PATH

    @property
    def unavailable_threshold_seconds(self) -> int:
        return self.UNAVAILABLE_THRESHOLD_SECONDS
    
    @property
    def network_source(self) -> str:
        return self.NETWORK_SOURCE

    @property
    def telemetry_path(self) -> str:
        return self.TELEMETRY_PATH

    @property
    def process_source(self) -> str:
        return self.PROCESS_SOURCE

settings = Settings()