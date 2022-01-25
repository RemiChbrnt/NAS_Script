# NAS_Script

## But du projet : auto-configurer un projet GNS3 avec un script Python

### Utilisation du script

- avoir un projet GNS3 ouvert à configurer

- avoir un fichier json à mettre en entrée contenant les directives de configuration souhaitées (par exemple, si ce router a besoin d'avoir BGP ou non)

- lancer le script python

### Fonctionnement

- Une fois le script lancé, le projet GNS3 ainsi que les dataclasses sont récupérer

- **Écriture des fichier de configuration (edit config dans GNS3):** adressage IP et mise en place de OSPF et MPLS pour tous routers et les autres devices. 

    Mise en place de BGP sur les routers sur lesquels c'est spécifié (dans le fichier json), ainsi que du filtrage BGP en fonction des communities auquels appartiennent les routers de bordure

- Placement de ces fichiers de configuration dans le projet GNS3



