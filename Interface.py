import json
from dataclasses import dataclass
from ipaddress import IPv4Address

@dataclass
class Interface:
    name: str

    ipv4: IPv4Address

