import json
from dataclasses import dataclass
import Interface
from typing import List, Union

from gns3fy import Node


@dataclass
class Router:
    name: str
    x: int
    y: int
    uid: str
    router_id: str
    as_number: int

    console_host: str
    console_port: int

    interfaces: list[Interface.Interface]

    def __post_init__(self):
        print(f"Routeur {self.name}, pos {self.x} : {self.y}")


    @staticmethod
    def from_node(node: Node, ri, as_number):
        return Router(name=node.name,
                      x=node.x, y=node.y, uid=node.node_id,
                      console_host=node.console_host, console_port=node.console,
                      router_id=ri, interfaces=[], as_number=as_number)


class Routers(dict):
    def get_by_uid(self, uid: str) -> Router:
        for router in self.values():
            if router.uid == uid:
                return router

    def add(self, router: Router):
        self[router.uid] = router

    def __getitem__(self, item) -> Router:
        return super().__getitem__(item)