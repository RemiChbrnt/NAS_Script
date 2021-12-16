import gns3fy as gns3
import Router
import Interface
import Link
from ipaddress import IPv4Address
import sys
from tabulate import tabulate


def router_list(gns3_server, project_id):
    routers = Router.Routers()

    router_i = 1  # Router id
    as_number = 7100  # As Number for all our Routers (we suppose that the config is our intern network)
    for node in gns3_server.get_nodes(project_id):
        obj = gns3.Node(project_id=project_id, node_id=node['node_id'], connector=gns3_server)
        obj.get()
        # We have imported our router as a dynamips image hence we verify we have the right object
        if obj.node_type == 'dynamips':
            # Creating our Router data object and adding it to the list
            # Our IPV4 address is initialized by default and is worthless, we modify it later
            routers.add(Router.Router.from_node(obj, str(IPv4Address(router_i)), as_number=as_number))
            router_i += 1
    return routers


def link_list(gns3_server, project_id, routers):
    ipv4 = 3232235520  # 192.168.0.0
    links = []  # initializing list
    for gns3_link in gns3_server.get_links(project_id):
        new_link = gns3.Link(connector=gns3_server, project_id=project_id, link_id=gns3_link['link_id'])
        new_link.get()

        router_side_a = routers.get_by_uid(new_link.nodes[0]['node_id'])
        router_side_b = routers.get_by_uid(new_link.nodes[1]['node_id'])

        if router_side_a is None or router_side_b is None:
            continue

        interface_a = Interface.Interface(
            name=new_link.nodes[0]['label']['text'],
            ipv4=IPv4Address(ipv4 + 1),
        )
        interface_b = Interface.Interface(
            name=new_link.nodes[1]['label']['text'],
            ipv4=IPv4Address(ipv4 + 2),
        )

        router_side_a.interfaces.append(interface_a)
        router_side_b.interfaces.append(interface_b)

        link_ab = Link.Link(
            uid=new_link.link_id,
            network4=IPv4Address(ipv4),
            side_a=router_side_a,
            side_b=router_side_b,
            int_a=interface_a,
            int_b=interface_b,
        )
        ipv4 += 4  # In order to have a 0 at the end of the Network address
        # print("link list" + str(link_ab))

        # Adds the interfaces to the routers

        links.append(link_ab)
    for lien in links:
        print(f'{lien.interface_a.ipv4} | {lien.side_a.name} > < {lien.side_b.name} | {lien.interface_b.ipv4}')
    return links


def get_config():
    def check_opened(project_list):
        if (project_list['status'] == 'opened'):
            return True
        return False

    try:
        gns3_server = gns3.Gns3Connector("http://localhost:3080")  # Gns3 server connector
    except Exception:
        print("Error : Cannot connect to GNS3 on localhost")

    try:
        # Get the ID of the opened GNS3 project (if there is only one opened)
        project_id = list(filter(check_opened, gns3_server.get_projects()))[0]['project_id']
    except Exception:
        print("Error : No GNS3 project is opened\n")
        exit(1)
    except IndexError:
        print("Error : Open only one GNS3 Project\n")
        exit(1)

    project = gns3.Project(project_id=project_id, connector=gns3_server)
    project.get()

    # print(project)
    print(f"Name: {project.name} -- Status: {project.status} -- Is auto_closed?: {project.auto_close}")

    routers = router_list(gns3_server, project_id)
    links = link_list(gns3_server, project_id, routers)

    return routers, gns3_server, project_id, links


if __name__ == '__main__':
    routers, gns3_server, project_id, links = get_config()