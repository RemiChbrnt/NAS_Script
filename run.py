import gns3fy as gns3
import os
import json
import Devices
import Interface
import Link
from ipaddress import IPv4Address
from configuration_commands import Commands
OPERATOR_FILE = 'json_file.json'


# Method to parse the JSON config and convert it into a Python dictionary
def jsonParse():
    objects = ""
    for line in open(OPERATOR_FILE):
        objects += line
    obj_dict = json.loads(objects)
    return obj_dict


def routemap_transport(config_file, community):
    config_file.write(f"!\n!\nroute-map TRANSPORT_IN permit 10\n match community 10\n set local-preference 50\n set community {community}\n!\n")
    config_file.write("route-map TRANSPORT_OUT permit 10\n match community 30\n continue\n")


def routemap_peer(config_file, community):
    config_file.write(f"!\n!\nroute-map PEER_IN permit 10\n match community 10\n set local-preference 100\n set community {community}\n!\n")
    config_file.write("route-map PEER_OUT permit 10\n match community 30\n continue\n")


def routemap_client(config_file, community):
    config_file.write(f"!\n!\nroute-map CLIENT permit 10\n match community 10\n set local-preference 150\n set community {community}\n!\n")


def communities(config_file, routerName, clients, ebgpNeighbors, config):
    config_file.write("ip community-list 10 permit internet\n")
    for neighbor in ebgpNeighbors:
        # Peers and Transport (Providers) must have access to the clients' routes
        if ebgpNeighbors[neighbor]["priority"] == "peer" or ebgpNeighbors[neighbor]["priority"] == "transport":
            for cli in clients:
                for cliName in cli:
                    if cli[cliName]["priority"] == "client":
                        config_file.write("ip community-list 30 permit {community}\n".format(community=str(cli[cliName]["as_number"])))
        # Peers also have access to other peers routes
        if ebgpNeighbors[neighbor]["priority"] == "peer":
            for cli in clients:
                for cliName in cli:
                    if cli[cliName]["priority"] == "peer" and cliName is not routerName:
                        config_file.write("ip community-list 30 permit {community}\n".format(community=str(cli[cliName]["as_number"])))


def init_config(router_i, config_file):
    config_file.write("!\n!\n!\n\n!\n! Last configuration change at {time}\n!\nversion 15.2\nservice timestamps debug "
                      "datetime msec\nservice timestamps log datetime msec".format(time = "09:34:45 UTC Thu Dec 2 "
                                                                                          "2021"))
    config_file.write("\n!\nhostname {nom_hostname}\n!\nboot-start-marker\nboot-end-marker\n!\n!\n!\nno aaa "
                      "new-model\nno ip icmp rate-limit unreachable\nip cef\n!\n!\n!\n!\n!\n!\nno ip domain "
                      "lookup\n".format(nom_hostname = router_i.name))
    config_file.write("no ipv6 cef\n!\n!\nmultilink bundle-name authenticated \n!\n!\n!\n!\n!\n!\n!\n!\n!\nip tcp "
                      "synwait-time 5\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\ninterface FastEthernet0/0\n no ip "
                      "address\n shutdown\n duplex full\n!\n")


def config_ip(router_i, interface_i, config_file, ospf, config): # ospf = boolean défini dans le json en entrée
    if ospf:
        if "neighbor" in config[router_i.name]:
            for neighbor in config[router_i.name]["neighbor"]:
                if config[router_i.name]["neighbor"][neighbor]["interface"] == interface_i.name:  # The link is eBGP, we don't have ospf in the config
                    config_file.write(
                        "interface {interface_name} \n ip address {ip_address} {mask}\n negotiation auto\n!\n".format(
                            interface_name=config[router_i.name]["neighbor"][neighbor]["interface"], ip_address=config[router_i.name]["neighbor"][neighbor]["ourIpv4"], mask="255.255.255.0"))
                else:
                    config_file.write("interface {interface_name} \n ip address {ip_address} {mask} \n ip ospf {"
                                      "num_area}\n negotiation auto\n!\n".format(interface_name = interface_i.name,
                                                                                 ip_address = interface_i.ipv4,
                                                                                 mask = "255.255.255.0", num_area = "4444 area 1"))


def interface_unconnected(config_file, interface_i):
    config_file.write("interface {nom_interface}\n no ip address\n shutdown\n duplex full\n!".format(nom_interface = interface_i.name))


def config_ospf(router_i, config_file, mpls): # mpls = boolean défini dans le json en entrée
    if mpls:
        config_file.write("router ospf {num_ospf}\n router-id {router_id}\n mpls ldp autoconfig\n!\n".format(num_ospf = "4444", router_id = router_i.router_id))
    else:
        config_file.write("router ospf {num_ospf}\n router-id {router_id}\n!\n".format(num_ospf = "4444", router_id = router_i.router_id))


def config_ibgp(router_i, neighborBgpIPs, config_file, config): # neighborBgpIPs = liste des ips des routeurs de la même AS qui ont bgp
    config_file.write("router bgp {as_number}\n bgp router-id {router_id}\n bgp log-neighbor-changes\n network {router_id} mask 255.255.255.255\n".format(as_number = router_i.as_number, router_id=router_i.router_id))

    # Advertising the necessary networks
    for rtr in config:  # Check for all routers
        if "neighbor" in config[rtr]:
            if rtr == router_i.name:    # This is the router we are configuring
                for neighbor in config[rtr]["neighbor"]:
                    config_file.write(" network {network} mask 255.255.255.0\n".format(network=config[rtr]["neighbor"][neighbor]["network"]))
            else:   # We are in another router of our network (not the one being configured)
                for neighbor in config[rtr]["neighbor"]:
                    for network in config[rtr]["neighbor"][neighbor]["advertised"]:
                        config_file.write(" network {network} mask 255.255.255.0\n".format(network=network))

    for ip in neighborBgpIPs:  # All these IPs are from BGP routers of our AS
            config_file.write(" neighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin=ip, as_number=router_i.as_number))
            config_file.write(" neighbor {ip_voisin} send-community\n".format(ip_voisin=ip, as_number=router_i.as_number))


def config_ebgp(router_i, ebgpNeighbors, config_file):  # ebgpNeighbors = liste des routeurs voisins d'une AS différente
    for neighbor in ebgpNeighbors:
        config_file.write(" neighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"], as_number=ebgpNeighbors[neighbor]["as_number"]))
        if ebgpNeighbors[neighbor]["priority"] == "client":
            config_file.write(" neighbor {ip_voisin} route-map CLIENT in\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"]))
        elif ebgpNeighbors[neighbor]["priority"] == "peer":
            config_file.write(" neighbor {ip_voisin} route-map PEER_IN in\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"]))
            config_file.write(" neighbor {ip_voisin} route-map PEER_OUT out\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"]))
        elif ebgpNeighbors[neighbor]["priority"] == "transport":
            config_file.write(" neighbor {ip_voisin} route-map TRANSPORT_IN in\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"]))
            config_file.write(" neighbor {ip_voisin} route-map TRANSPORT_OUT out\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"]))

def end1_config(config_file):
    config_file.write("!\nip forward-protocol nd\n!\n")

def end2_config(config_file):
    config_file.write("!\nno ip http server\nno ip http secure-server\n")
    
def end3_config(config_file):
    config_file.write("!\n!\n!\ncontrol-plane\n!\n!\nline con 0\n exec-timeout 0 0\n privilege level 15")
    config_file.write("\n logging synchronous\n stopbits 1\nline aux 0\n exec-timeout 0 0\n privilege level 15\n logging synchronous\n stopbits 1\nline vty 0 4\n login\n!\n!\nend")

def config_pc(pc_i, config_file):
    config_file.write("set pcname {pc_name}\nip {ip_pc} {ip_router} {mask}".format(pc_name = pc_i.name, ip_pc = "10.10.12.2", ip_router = "10.10.12.1", mask = 24)) #A COMPLETER QUAND DATACLASS TERMINAL FINIE


def router_list(gns3_server, project_id):
    routers = Devices.Routers()

    routerNum = 1+2**8+2**16+2**24  # Router id
    vpcNum = 1
    as_number = 7200  # As Number for all our Routers (we suppose that the config is our intern network)
    for node in gns3_server.get_nodes(project_id):
        obj = gns3.Node(project_id=project_id, node_id=node['node_id'], connector=gns3_server)
        obj.get()
        # We have imported our router as a dynamips image hence we verify we have the right object
        if obj.node_type == 'dynamips':
            # Creating our Router data object and adding it to the list
            # Our IPV4 address is initialized by default and is worthless, we modify it later
            routers.add(Devices.Router.from_node(obj, str(IPv4Address(routerNum)), as_number=as_number))
            routerNum += 1+2**8+2**16+2**24
        if obj.node_type == 'vpcs':
            # Creating our VPC data object and adding it to the list
            vpcNum += 1
    return routers


def link_list(gns3_server, project_id, routers, config):
    ipv4 = 167772160  # 10.0.0.0

    links = []  # initializing list
    for gns3_link in gns3_server.get_links(project_id):
        new_link = gns3.Link(connector=gns3_server, project_id=project_id, link_id=gns3_link['link_id'])
        new_link.get()

        router_side_a = routers.get_by_uid(new_link.nodes[0]['node_id'])
        router_side_b = routers.get_by_uid(new_link.nodes[1]['node_id'])

        if router_side_a is None or router_side_b is None:
            continue

        # Defining the interfaces' names
        int_a_name = "unnamed"
        int_b_name = "unnamed"
        if new_link.nodes[0]['label']['text'][0] == 'g':
            int_a_name = "GigabitEthernet" + new_link.nodes[0]['label']['text'][1:]
        if new_link.nodes[1]['label']['text'][0] == 'g':
            int_b_name = "GigabitEthernet" + new_link.nodes[1]['label']['text'][1:]

        ipv4_a = IPv4Address(ipv4 + 1)
        ipv4_b = IPv4Address(ipv4 + 2)
        network = IPv4Address(ipv4)

        eBGP_link = False
        if "neighbor" in config[router_side_a.name]:    # Handling eBGP links
            for neighbor in config[router_side_a.name]["neighbor"]:
                if neighbor == router_side_b.name:  # We have an eBGP link
                    ipv4_a = config[router_side_a.name]["neighbor"][neighbor]["ourIpv4"]
                    ipv4_b = config[router_side_a.name]["neighbor"][neighbor]["hisIpv4"]
                    network = config[router_side_a.name]["neighbor"][neighbor]["network"]
                    eBGP_link = True
        if "neighbor" in config[router_side_b.name]:  # Handling eBGP links
            for neighbor in config[router_side_b.name]["neighbor"]:
                if neighbor == router_side_a.name:  # We have an eBGP link
                    ipv4_a = config[router_side_b.name]["neighbor"][neighbor]["ourIpv4"]
                    ipv4_b = config[router_side_b.name]["neighbor"][neighbor]["hisIpv4"]
                    network = config[router_side_b.name]["neighbor"][neighbor]["network"]
                    eBGP_link = True
        if eBGP_link == False:  # We have an internal link (no eBGP)
            ipv4 += 256  # In order to have a 0 at the end of the Network address

        interface_a = Interface.Interface(
            name=int_a_name,
            ipv4=ipv4_a,
        )
        interface_b = Interface.Interface(
            name=int_b_name,
            ipv4=ipv4_b,
        )

        # Appending the interfaces to the routers
        router_side_a.interfaces.append(interface_a)
        router_side_b.interfaces.append(interface_b)

        link_ab = Link.Link(
            uid=new_link.link_id,
            network4=network,
            side_a=router_side_a,
            side_b=router_side_b,
            int_a=interface_a,
            int_b=interface_b,
        )


        # print("link list" + str(link_ab))

        links.append(link_ab)
    for lien in links:
        print(f'{lien.interface_a.ipv4} | {lien.side_a.name} > < {lien.side_b.name} | {lien.interface_b.ipv4}')
    return links


def get_config(config):
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
    links = link_list(gns3_server, project_id, routers, config)

    return routers, gns3_server, project_id, project.path, links


if __name__ == '__main__':

    config = jsonParse()

    routers, gns3_server, project_id, project_path, links = get_config(config)

    ebgpClients = []  # The client Routers and their characteristics
    for rtr in config:
        if "neighbor" in config[rtr]:
            ebgpClients.append(config[rtr]["neighbor"])

    #print(ebgpClients)

    # print(project_path)

    for routerID in routers:

        router = routers[routerID]

        if router.name in config:      # If the router is a client, we suppose it is already configured and that this configuration is known
            if "client" in config[router.name]:
                if config[router.name]["client"]:
                    continue

        print("Writing config for router %s of id %s" % (router.name, routerID))

        ospf = True
        mpls = True
        bgp = False
        ebgpNeighbors = []

        if router.name in config:
            if "bgp" in config[router.name]:
                bgp = config[router.name]["bgp"]
            if "neighbor" in config[router.name]:
                ebgpNeighbors = config[router.name]["neighbor"]

        # Creating the router config file if it doesn't exist
        router_config_path = project_path + "\project-files\dynamips\\" + router.uid + "\\configs"
        if not os.path.isdir(router_config_path):
            os.mkdir(router_config_path)
        file_name = router_config_path + "\\i" + router.name[1:] + "_startup-config.cfg"
        # print(file_name)
        # Creating the res file if it doesn't exist
        if not os.path.isdir("./res"):
            os.mkdir("./res")
        name = "res/edit_config%s.cfg" % router.name
        fichier_res = open(name, "w")
        file_conf = open(file_name, "w")
        init_config(router, fichier_res)
        init_config(router, file_conf)
        for interface in router.interfaces:

            isConnected = False
            # Si notre interface est utilisée par un routeur qui est dans la liste links -> c'est une interface active
            for lien in links:
                if lien.side_a.name == router.name:
                    if lien.int_a.name == interface.name:
                        isConnected = True
                if lien.side_b.name == router.name:
                    if lien.int_b.name == interface.name:
                        isConnected = True

            if isConnected:
                config_ip(router, interface, fichier_res, ospf, config)
                config_ip(router, interface, file_conf, ospf, config)
            else:
                interface_unconnected(fichier_res, interface)
                interface_unconnected(file_conf, interface)
        if ospf:
            config_ospf(router, fichier_res, mpls)
            config_ospf(router, file_conf, mpls)


        if bgp:
            print ("Bgp is on for " + router.name)
            bgpNeighborIPs = []
            bgpNeighbors = []
            # Adding the BGP neighbors' IPs within our AS
            for lien in links:
                if lien.side_a.name == router.name and "bgp" in config[lien.side_b.name]:
                    if config[lien.side_b.name]["bgp"]:     # If bgp is set to True
                        bgpNeighborIPs.append(lien.int_b.ipv4)
                        bgpNeighbors.append(lien.side_b)
                if lien.side_b.name == router.name and "bgp" in config[lien.side_a.name]:
                    if config[lien.side_a.name]["bgp"]:     # If bgp is set to True
                        bgpNeighborIPs.append(lien.int_a.ipv4)
                        bgpNeighbors.append(lien.side_a)

            addedNewIP = True
            while addedNewIP:     # Iterate for our BGP neighbors' BGP neighbors until we have no more IP addition -> full BGP routers within the AS
                addedNewIP = False
                for rtr in bgpNeighbors:
                    for lien in links:
                        if lien.side_a == rtr and "bgp" in config[lien.side_b.name] and lien.side_b not in bgpNeighbors and lien.side_b != router:
                            if config[lien.side_b.name]["bgp"]:  # If bgp is set to True
                                bgpNeighborIPs.append(lien.int_b.ipv4)
                                bgpNeighbors.append(lien.side_b)
                                addedNewIP = True
                        if lien.side_b == rtr and "bgp" in config[lien.side_a.name] and lien.side_a not in bgpNeighbors and lien.side_a != router:
                            if config[lien.side_a.name]["bgp"]:  # If bgp is set to True
                                bgpNeighborIPs.append(lien.int_a.ipv4)
                                bgpNeighbors.append(lien.side_a)
                                addedNewIP = True

            config_ibgp(router, bgpNeighborIPs, fichier_res, config)
            config_ibgp(router, bgpNeighborIPs, file_conf, config)
            config_ebgp(router, ebgpNeighbors, fichier_res)
            config_ebgp(router, ebgpNeighbors, file_conf)

        end1_config(fichier_res) 
        end1_config(file_conf)

        if bgp :
            communities(fichier_res, router.name, ebgpClients, ebgpNeighbors, config)
            communities(file_conf, router.name, ebgpClients, ebgpNeighbors, config)

        end2_config(fichier_res)         
        end2_config(file_conf)

        if bgp :
            for neighbor in ebgpNeighbors:
                communityNum = str(ebgpNeighbors[neighbor]["as_number"])
                if ebgpNeighbors[neighbor]["priority"] == "client":
                    routemap_client(fichier_res, communityNum)
                    routemap_client(file_conf, communityNum)
                elif ebgpNeighbors[neighbor]["priority"] == "peer":
                    routemap_peer(fichier_res, communityNum)
                    routemap_peer(file_conf, communityNum)
                elif ebgpNeighbors[neighbor]["priority"] == "transport":
                    routemap_transport(fichier_res, communityNum)
                    routemap_transport(file_conf, communityNum)

        end3_config(fichier_res)         
        end3_config(file_conf)

        fichier_res.close()
        file_conf.close()


    

