from sim.api import *
from sim.basics import *

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    def __init__(self):
        self.routingTable = {} #map of maps
        self.neighbors = {}
        self.forwardingTable = RoutingUpdate()
        self.toSend = False

    def handle_rx (self, packet, port):
        if isinstance(packet, DiscoveryPacket):
            incoming = packet.src
            if packet.is_link_up: #if packet is up or down
                if incoming not in self.neighbors:
                    self.neighbors[incoming] = port
                    self.routingTable[incoming] = {}
                    self.routingTable[incoming][incoming] = packet.latency
                else:
                    self.routingTable[incoming][incoming] = packet.latency
            else: #packet down
                self.routingTable[incoming][incoming] = float("inf")
            toSend = True
            self.find_min_fTable()
            if self.toSend:
                for neighbor in self.routingTable:
                    if isinstance(neighbor, HostEntity) == False:
                        self.create_route(neighbor)
        elif isinstance(packet, RoutingUpdate):
            n = packet.src
            d = packet.all_dests()
            for dest in packet.all_dests(): 
                self.routingTable[n][dest] = packet.get_distance(dest) + self.routingTable[n][n]
            self.find_min_fTable()
            for neighbor in self.neighbors: #for all neighbors
                if isinstance(neighbor, HostEntity) == False:
                    self.create_route(neighbor)
        else: #this is a data packet
            dest = packet.dst
            packet.ttl = packet.ttl -1
            if dest != self and dest in self.forwardingTable.paths:
                if self.forwardingTable.paths[dest][0] != float("inf"):
                    self.send(packet, port = self.neighbors[self.forwardingTable.paths[dest][1]])

    def find_min_fTable(self):
        updates = {}
        for n in self.routingTable:
            for d in self.routingTable[n]:
                if d not in updates and self.routingTable[n][d] != float("inf"):
                    updates[d] = (self.routingTable[n][d], n)
                else:
                    if self.routingTable[n][d] < updates[d][0]:
                        updates[d] = (self.routingTable[n][d], n)
        if updates != self.forwardingTable.paths:
            self.forwardingTable.paths = updates
            self.toSend = True
            
    def create_route(self, neighbor):
        #neighbor is what we don't want to be
        route = RoutingUpdate() #create new routing update object
        for n in self.forwardingTable.paths: #for neighbors in table
            if n != neighbor and self.forwardingTable.paths[n][1] != neighbor:
                route.add_destination(n, self.forwardingTable.paths[n][0])
        if self.toSend:
            #print route.paths
            self.send(route, port = self.neighbors[neighbor])
            self.toSend = False
