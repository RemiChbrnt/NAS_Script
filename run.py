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


def config_ibgp(router_i, voisins_bgp, config_file, config): # voisins_bgp = liste des liens avec les routeurs de la même AS qui ont bgp
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

    for voisins in voisins_bgp : # Les routeurs configures ici sont tous dans notre AS, on est en ibgp
        if voisins.side_a == router_i :
            # Pour chaque voisin on écrit les lignes de config
            config_file.write(" neighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin = voisins.int_b.ipv4, as_number= router_i.as_number))

        elif voisins.side_b == router_i :
            # Pour chaque voisin on écrit les lignes de config
            config_file.write(" neighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin = voisins.int_a.ipv4, as_number= router_i.as_number))


def config_ebgp(router_i, ebgpNeighbors, config_file):  # ebgpNeighbors = liste des routeurs voisins d'une AS différente
    for neighbor in ebgpNeighbors:
        config_file.write(" neighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin=ebgpNeighbors[neighbor]["hisIpv4"], as_number=ebgpNeighbors[neighbor]["as_number"]))

def end_config(config_file):
    config_file.write("ip forward-protocol nd\n!\n!\nno ip http server\nno ip http secure-server\n!\n!\n!\n!\ncontrol-plane\n!\n!\nline con 0\n exec-timeout 0 0\n privilege level 15")
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
    ipv4 = 3232235520  # 192.168.0.0
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
            ipv4 += 4  # In order to have a 0 at the end of the Network address

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

    # print(project_path)

    for routerID in routers:

        router = routers[routerID]
        print("Writing config for router %s of id %s" % (router.name, routerID))

        if router.name in config:      # If the router is a client, we suppose it is already configured and that this configuration is known
            if "client" in config[router.name]:
                if config[router.name]["client"]:
                    continue

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
            bgpNeighbors = []
            # 1) on ajoute nos liens de routeurs voisins qui ont bgp
            for lien in links:
                if lien.side_b.name in config:
                    if lien.side_a.name == router.name and "bgp" in config[lien.side_b.name]:
                        if config[lien.side_b.name]["bgp"]:     # If bgp is set to True
                            bgpNeighbors.append(lien)
                if lien.side_a.name in config:
                    if lien.side_b.name == router.name and "bgp" in config[lien.side_a.name]:
                        if config[lien.side_a.name]["bgp"]:     # If bgp is set to True
                            bgpNeighbors.append(lien)
            config_ibgp(router, bgpNeighbors, fichier_res, config)
            config_ibgp(router, bgpNeighbors, file_conf, config)
            config_ebgp(router, ebgpNeighbors, fichier_res)
            config_ebgp(router, ebgpNeighbors, file_conf)
            fichier_res.write("!\n")
            file_conf.write("!\n")

        end_config(fichier_res)
        end_config(file_conf)

        fichier_res.close()
        file_conf.close()

    # A RAJOUTER : POUR CHAQUE TERMINAL AUSSI

    # 4) selon les informations du json appeler telle ou telle fonction de config et compléter le fichier editconfig 
    # 5) (Rémi) envoyer les fichiers editconfig dans gns3 au bon endroit
    

