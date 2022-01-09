import gns3fy as gns3
import Router
import Interface
import Link
from ipaddress import IPv4Address
from configuration_commands import Commands
from tabulate import tabulate


def init_config(router_i, config_file):
    config_file.write("!\n!\n!\n\n!\n! Last configuration change at {time}\n!\nversion 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec".format(time = "09:34:45 UTC Thu Dec 2 2021"))
    config_file.write("\n!\nhostname {nom_hostname}\n!\nboot-start-marker\nboot-end-marker\n!\n!\n!\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\n!\n!\n!\n!\n!\n!\nno ip domain lookup\n".format(nom_hostname= router_i.name))
    config_file.write("no ipv6 cef\n\n!\n!\nmultilink bundle-name authenticated \n!\n!\n!\n!\n!\n!\n!\n!\n!\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\n!\n")

def config_ip(interface_i, config_file, ospf): #ospf = boolean défini dans le json en entrée
    if ospf:
        config_file.write("interface {interface_name} \n\rip address {ip_address} {mask} \n\rip ospf {num_area}\n\rnegotiation auto\n!\n").format(interface_name = interface_i.name, ip_address = interface_i.ipv4, mask = "255.255.255.0", num_area = "4444 area 1")
    else:
        config_file.write("interface {interface_name} \n\rip address {ip_address} {mask}\n\rnegotiation auto\n!\n".format(interface_name = interface_i.name, ip_address = interface_i.ipv4, mask = "255.255.255.0"))


def interface_unconnected(config_file, interface_i):
    config_file.write("interface {nom_interface}\n\rno ip address\n\rshutdown\n\rduplex full\n!".format(nom_interface = interface_i.name))


def config_ospf(router_i, config_file, mpls): #mpls = boolean défini dans le json en entrée
    if mpls:
        config_file.write("router ospf {num_ospf}\n\rrouter-id {router_id}\n\rmpls ldp autoconfig\n!\n".format(num_ospf = "4444", router_id = router_i.router_id))
    else:
        config_file.write("router ospf {num_ospf}\n\rrouter-id {router_id}\n!\n".format(num_ospf = "4444", router_id = router_i.router_id))

def config_bgp(router_i, voisins_bgp, config_file): #voisins_bgp = liste des liens avec les routeurs voisins qui ont bgp
    config_file.write("router bgp {as_number}\n\rbgp router-id {router_id}\n\rbgp log-neighbor-changes\n\rnetwork {router_id} mask 255.255.255.255\n".format(as_number = router_i.as_number, router_id=router_i.router_id))
  
    for voisins in voisins_bgp :
        if voisins.side_a == router_i :
            #si on a un/des voisins bgp dans notre as
            if voisins.side_b.as_number == router_i.as_number :
                #pour chaque voisin on écrit les lignes de config
                config_file.write("\rneighbor {ip_voisin} remote-as {as_number}\n\rneighbor {ip_voisin} next-hop-self\n".format(ip_voisin = voisins.int_b.ipv4, as_number= router_i.as_number))

            #si on a un/des voisins bgp dans un autre as
            else :
                config_file.write("\rneighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin = voisins.int_b.ipv4, as_number = voisins.side_b.as_number))
        elif voisins.side_b == router_i :
            if voisins.side_a.as_number == router_i.as_number :
                #pour chaque voisin on écrit les lignes de config
                config_file.write("\rneighbor {ip_voisin} remote-as {as_number}\n\rneighbor {ip_voisin} next-hop-self\n".format(ip_voisin = voisins.int_a.ipv4, as_number= router_i.as_number))

            #si on a un/des voisins bgp dans un autre as
            else :
                config_file.write("\rneighbor {ip_voisin} remote-as {as_number}\n".format(ip_voisin = voisins.int_a.ipv4, as_number = voisins.side_a.as_number))

    config_file.write("!\n")

    
def end_config(config_file):
    config_file.write("ip forward-protocol nd\n!\n!\nno ip http server\nno ip http secure-server\n!\n!\n!\n!\ncontrol-plane\n!\n!\nline con 0\n\r exec-timeout 0 0\n\r privilege level 15")
    config_file.write("\n\rlogging synchronous\n\rstopbits 1\nline aux 0\n\rexec-timeout 0 0\n\rprivilege level 15\n\rlogging synchronous\n\rstopbits 1\nline vty 0 4\n\rlogin\n!\n!\nend")

def config_pc(pc_i, config_file):
    config_file.write("set pcname {pc_name}\nip {ip_pc} {ip_router} {mask}".format(pc_name = pc_i.name, ip_pc = "10.10.12.2", ip_router = "10.10.12.1", mask = 24)) #A COMPLETER QUAND DATACLASS TERMINAL FINIE


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

    # Now that we have the configuration, we can modify it
    # We first modify all the links for the ip addresses to match those chosen
    # -----------------------------------------------------------------------

    # 1) ouvrir le fichier JSON qui contient les règles de configuration à appliquer au projet

    #json_file = open("config_json.txt", "r")

    # 2) Parser ce fichier 
    

    # 3) Pour chaque device, ouvrir un fichier texte pour ecrire le edit config
    for router in routers :

        #Création des boolean qui indiqueront a chaque routeur la configuration à adapter
        ospf = False
        mpls = False
        bgp = False

        fichier = open("edit_config.txt", "x")
        init_config(router, fichier)
        for interface in router.interfaces :

            isConnected = False
            #Si notre interface est utilisée par un routeur qui est dans la liste links -> c'est une interface active
            for lien in links :
                if lien.side_a.name == router.name :
                    if lien.int_a.name == interface :
                        isConnected = True
                if lien.side_b.name == router.name :
                    if lien.int_b.name == interface :
                        isConnected = True

            if isConnected :
                config_ip(interface, fichier, ospf) #remplacer True par boolean ospf parsé quand on aura le json
            else :
                interface_unconnected(fichier, interface)

        if ospf :
            config_ospf(router, fichier, mpls)

        if bgp :
            voisins_bgp = []
            
            config_bgp(router, voisins_bgp, fichier)

        end_config(router, fichier)
        fichier.close()

    #A RAJOUTER : POUR CHAQUE TERMINAL AUSSI

    # 4) selon les informations du json appeler telle ou telle fonction de config et compléter le fichier editconfig 
    # 5) (Rémi) envoyer les fichiers editconfig dans gns3 au bon endroit
    

