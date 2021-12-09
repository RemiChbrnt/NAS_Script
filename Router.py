import json
from dataclasses import dataclass
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

    # type: List[Interface]
    interfaces: list

    @staticmethod
    def from_node(node: Node, ri, asn):
        return Router(name=node.name,
                      x=node.x, y=node.y, uid=node.node_id,
                      console_host=node.console_host, console_port=node.console,
                      router_id=ri, interfaces=[], as_number=asn)


class Routers(dict):
    # type: List[Router]
    def get_by_uid(self, uid: str) -> Router:
        for router in self.values():
            if router.uid == uid:
                return router

    def add(self, router: Router):
        self[router.name] = router

    def __getitem__(self, item) -> Router:
        return super().__getitem__(item)