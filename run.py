import gns3fy as gns3
from tabulate import tabulate

gns3_server = gns3.Gns3Connector("http://localhost:3080")

gns3_server.get_version()




print(
        tabulate(
            gns3_server.projects_summary(is_print=False),
            headers=["Project Name", "Project ID", "Total Nodes", "Total Links", "Status"],
        )
    )

#lab = gns3.Project(name="NAS", connector=gns3_server)

#lab.get()
#print(lab)