# NAS_Script

Auteurs : Rémi Chabrant, Estelle Monier, Agnès Thouvenin, Jade Archer, Olga Cosculluela Palacin

## But du projet : auto-configurer un projet GNS3 avec un script Python

### Utilisation du script run.py

- avoir un projet GNS3 ouvert à configurer

- avoir un fichier json à mettre en entrée contenant les directives de configuration souhaitées (par exemple, si ce router a besoin d'avoir BGP ou non)

- lancer le script python (commande: python3 run.py)

### Fonctionnement

- Une fois le script lancé, le projet GNS3 ainsi que les dataclasses sont récupérées

- **Écriture des fichier de configuration (edit config dans GNS3):** adressage IP et mise en place de OSPF et MPLS pour tous routers et les autres devices. 

    Mise en place de BGP sur les routers sur lesquels c'est spécifié (dans le fichier json). 
    
    Mise en place également des permissions des routes BGP en fonction des communities auquelles appartiennent les routers de bordure (selon si ce sont des clients, des peers ou des providers). Si ce sont des clients, toutes les routes leur sont permises, si ce sont des peers, les routes pour accéder aux clients et aux autres peers leur sont permises, et si ce sont des providers ils ont juste accès aux routes des clients.

- Placement de ces fichiers de configuration dans le projet GNS3











