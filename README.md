# NAS_Script

## Useful Links

[Python Library](https://davidban77.github.io/gns3fy/api_reference/)

[MarkDown Syntax for ReadMe File](https://www.markdownguide.org/basic-syntax)


In GNS3, go to Edit -> Preferences -> Server, Untick **Protect Server with password** and tick **Allow console connections to any local IP Address**

Then download the developer version of [gns3fy](https://github.com/davidban77/gns3fy/tree/developer)

## Objectifs

- pour utiliser notre solution, il faut écrire un **fichier de configuration** simple résumant la config : préciser les routers, les liens entre eux, et les Providers Edge qui ont BGP activé

- dans ce fichier de configuration, pas besoin de préciser l'implémentation de ospf ou mpls par exemple car on sait qu'il faut le faire sur tous les routers

- ce fichier de configuration (json) peut générer des fichiers de configuration plus complets à donner au script python pour permettre de réaliser la configuration gns3 de manière automatique

- il faut un json pour le provider et un json pour le client

