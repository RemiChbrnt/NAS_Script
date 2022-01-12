import json
from ipaddress import IPv4Address
from dataclasses import dataclass
import Interface
import Devices



@dataclass
class Link:
    uid: str

    network4: IPv4Address

    side_a: Devices.Router
    side_b: Devices.Router

    int_a: Interface.Interface
    int_b: Interface.Interface
    # network4_display: str = "10/8"

    def __post_init__(self):
        print(f"Link uid {self.uid}, network {self.network4}, between {self.side_a.name} and {self.side_b.name}")

    @property
    def interface_a(self):
        def get_interface_name(int):
            if int.name == self.int_a.name:
                return True
            return False

        return list(filter(get_interface_name, self.side_a.interfaces))[0]

    @property
    def interface_b(self):
        def get_interface_name(int):
            if int.name == self.int_b.name:
                return True
            return False

        return list(filter(get_interface_name, self.side_b.interfaces))[0]

    def __str__(self):
        return "Router {name_a} on interface {interface_b} - Router {name_b} on interface {interface_a} ".format(
            name_a=self.side_a.name, interface_a=self.int_a, name_b=self.side_b.name,
            interface_b=self.int_b)

    @property
    def name(self):
        return "Router {name_a} - Router {name b}".format(
            name_a=self.side_a.name, name_b=self.side_b.name
        )
