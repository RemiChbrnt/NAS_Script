import Router
from ipaddress import IPv4Address
from dataclasses import dataclass
import Interface


@dataclass
class Link:
    uid: str

    network4: IPv4Address

    side_a: Router.Router
    side_b: Router.Router

    interface_a: Interface.Interface
    interface_b: Interface.Interface
    # network4_display: str = "10/8"

    @property
    def interface_a(self):
        def get_interface_name(int):
            if int.name == self.interface_a:
                return True
            return False

        return list(filter(get_interface_name, self.side_a.interfaces))[0]

    @property
    def interface_b(self):
        def get_interface_name(int):
            if int.name == self.interface_b:
                return True
            return False

        return list(filter(get_interface_name, self.side_b.interfaces))[0]

    def __str__(self):
        return "Router {name_a} on interface {interface_b} - Router {name_b} on interface {self.int_a} ".format(
            name_a=self.side_a.name, interface_a=self.interface_a, name_b=self.side_b.name,
            interface_b=self.interface_b)

    @property
    def name(self):
        return "Router {name_a} - Router {name b}".format(
            name_a=self.side_a.name, name_b=self.side_b.name
        )


SIDE_A = 'a'
SIDE_B = 'b'
