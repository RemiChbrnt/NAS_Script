import time

class Commands:

     def sendCommand(self, message: str):
        self.socket.send(f"{message} ".encode('utf-8'))
        time.sleep(0.1)  # Petite pause sinon on envoie les commandes t

    #Configuracion ipv4
     def configureTerminal(self):
        self.sendCommand("end")  
        self.sendCommand("conf t")
    
     def configIPv4(self, interface, address):
        self.configureTerminal()
        self.sendCommand(f"int {interface}")
        self.sendCommand(f"IPv4 address {address[0]} {address[1]}")
        self.sendCommand("no shutdown")
        self.sendCommand("end")
        self.sendCommand("end")

    #Configuracion OSPF
     def configOSPF(self, address):
        self.configureTerminal()
        self.sendCommand("router ospf 4444")
        self.sendCommand(f"router-id {address}")
        

     def NeighbourOSPF(self, neighbours):
        self.configureTerminal()
        self.sendCommand("router ospf 1")
        for num in neighbours:
            self.sendCommand(f"network {num[0]} {num[1]} area {num[2]}")

     def OSPFInterface(self, interface, area):
        self.configureTerminal()
        self.sendCommand(f"int {interface}")
        self.sendCommand(f"ip ospf 4444 area {area}")
        self.sendCommand("end")

     #Configuracion mpls
     def configMPLS(self, address):
        self.configureTerminal()
        self.sendCommand("router ospf 4444")
        self.sendCommand(f"router-id {address}")
        self.sendCommand("mpls ldp autoconfig")

     #Configuracion BGP
     def activateBGP(self, asNumber, processID):
         self.configureTerminal()
         self.sendCommand(f"router bgp {asNumber}")
         self.sendCommand(f"bgp router-id {processID}")

     def connectToClientBGP(self,processID, tabNeighborsClients, tabNeighborsProvider, asNumberProvider):
         #TabNeighbors: asNumber: IP
         self.activateBGP(self, asNumberProvider, processID)
         for asNumber, ipAddress in tabNeighborsClients.items():
            self.sendCommand(f"neighbor {ipAddress} remote-as {asNumber}")
         for asNumber, ipAddress in tabNeighborsProvider.items():
            self.sendCommand(f"neighbor {ipAddress} remote-as {asNumber} ")
            self.sendCommand(f"neighbor {ipAddress} next-hop-self")
         self.sendCommand(f"network {processID} mask 255.255.255.255")
         self.sendCommand("end")

     def connectToProviderBGP(self, processID, asNumberProvider, ipAdressProvider, asNumberClient, lanNetwork):
        #LanNetwork: Address reseau: mask 
         self.activateBGP(self, asNumberClient, processID)
         self.sendCommand(f"neighbor {ipAdressProvider} remote-as {asNumberProvider}")
         for adReseau, mask in lanNetwork.items():
            self.sendCommand(f"network {adReseau} mask {mask}")
         self.sendCommand("end")

   # Filtrage BGP
     def filtrageBGP(self, name, sourcePrefix, destinationPrefix, mapTag, sequenceNumber, sequenceNumber2, ipAddress):
        self.configureTerminal()
        self.sendCommand("ipv6 access-list {name}")
        self.sendCommand(f"permit {sourcePrefix} {destinationPrefix} ")
        self.sendCommand(f"route-map {mapTag} deny {sequenceNumber} ")
        self.sendCommand(f"match ipv6 address {name} ")
        self.sendCommand("exit")
        self.sendCommand(f"route-map {mapTag} permit {sequenceNumber2} ")
        self.sendCommand(f"neighbor {ipAddress} route-map {mapTag} in ")
        
     def filtragePath(self, name, mapTag, sequenceNumber, nrList, regexp, sequenceNumber2, ipAddress):
        self.configureTerminal()       
        self.sendCommand(f"route-map {mapTag} permit {sequenceNumber} ")
         #(by default local pref is 100, so choose a value higher than this)
        self.sendCommand(f"set local-preference 110 ")
        self.sendCommand("exit")
        self.sendCommand(f"neighbor {ipAddress} route-map {mapTag} in ")
        self.sendCommand("exit")
         
        self.sendCommand(f"ip as-path access-list{nrList} permit {regexp} ")
        self.sendCommand(f"route-map {mapTag} deny {sequenceNumber} ")
        self.sendCommand(f"match as-path {name} ")
        self.sendCommand("exit")
         #(by default, there is an unwritten route-map deny, so we need to force a permit)
        self.sendCommand(f"route-map {mapTag} permit {sequenceNumber2} ")
        self.sendCommand(f"neighbor {ipAddress} route-map {mapTag} out ")






       
