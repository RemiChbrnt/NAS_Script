import gns3fy as gns3
from Router import Router, Routers
from ipaddress import IPv4Address
from tabulate import tabulate

def router_list(gns3_server, project_id):

    routers = Routers()

    router_i = 1    # Router id
    as_number = 7100     # As Number for all our Routers (we suppose that the config is our intern network)
    for node in gs.get_nodes(project_id):
        obj = gns3.Node(project_id=project_id, node_id=node['node_id'], connector=gns3_server)
        obj.get()
        # We have imported our router as a dynamips image hence we verify we have the right object
        if obj.node_type == 'dynamips':
            # Creating our Router data object and adding it to the list
            # Our IPV4 address is initialized by default and is worthless, we modify it later
            routers.add(Router.from_node(obj, str(IPv4Address(router_i)), as_number=as_number))
            router_i += 1
    return routers


def get_config():

    def check_opened(project_list):
        if(project_list['status'] == 'opened'):
            return True
        return False
    try:
        gns3_server = gns3.Gns3Connector("http://localhost:3080") #Gns3 server connector
    except StandardError:
        print("Error : Cannot connect to GNS3 on localhost")

    try:
        # Get the ID of the opened GNS3 project (if there is only one opened)
        project_id = list(filter(check_opened, gns3_server.get_projects()))[0]['project_id']
    except StandardError :
        print("Error : No GNS3 project is opened\n")
        exit(1)
    except IndexError:
        print("Error : Open only one GNS3 Project\n")
        exit(1)

    project = gns3.Project(project_id=project_id, connector=gns3_server)
    project.get()

    routers = router_list(gns3_server, project_id)
    links = enumerate_links(gns3_server, project_id, routers)

    return routers, gns3_server, project_id, links


if __name__ == '__main__':

    lab = gns3.Project(name="NAS", connector=gns3_server)
    lab.get()
    print(lab)

    print(f"Name: {lab.name} -- Status: {lab.status} -- Is auto_closed?: {lab.auto_close}")
