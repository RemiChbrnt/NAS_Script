import gns3fy as gns3
import ipaddress
from gns3fy.gns3fy import Gns3Connector, Project
from tabulate import tabulate
import json

gns3_server = gns3.Gns3Connector("http://localhost:3080")

gns3_server.get_version()

# Abrimos el proyecto vacio para empezar a crear los objetos
NAS = Project(name="test", project_id='fb471fb8-e60c-4f1d-bb24-d11221423ea3', connector=gns3_server)
NAS.create()
print(NAS.status)

# Creamos los routers
num_routers = 5
for num in range(1, num_routers):
    NAS.create_node(name=('Router' + str(num)), template='Cisco 7200 124-24.T5')

# Creamos los links
num_links = 4
# Este es el ultimo link
NAS.create_link('Router' + str(num_links), 'GigabitEthernet1/0', 'Router1', 'GigabitEthernet2/0')
for num in range(1, num_links):
    NAS.create_link('Router' + str(num), 'GigabitEthernet1/0', 'Router' + str(num + 1), 'FastEthernet0/0')

# Empezamos a configurar ipv4
"""""
try:
    end = int(end)

    net = int(ipaddress.IPv4Address(interface['ipv4_network']))
    print(str(ipaddress.IPv4Address(end+net)))
except ipaddress.AddressValueError:
    print('error') 
"""""
"openconfig-if-ip:ipv4"

# Imprimimos todo lo que tenemos en el proyecto

print(
    tabulate(
        gns3_server.projects_summary(is_print=False),
        headers=["Project Name", "Project ID", "Total Nodes", "Total Links", "Status"],
    )
)
with open("config.json", "w") as outfile:
    json.dump(data, outfile)

# lab.get()
# print(lab)