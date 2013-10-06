class LSRouter (Entity):
    def __init__(self):
        self.graph = Graph()
        self.forwarding_table = dict()
        self.port_lookup = dict()
        self.list_of_hosts = set()
        self.processed_packets = set()

    def handle_rx(self, packet, port):
        if isinstance(packet, DiscoveryPacket):
            self._handle_discovery(packet, port)
        elif isinstance(packet, RoutingUpdate):
            self._handle_routing_update(packet, port)
        else:
            self._handle_data(packet, port)

    def _handle_discovery(self, packet, port):
        source = packet.src # source is another word for neighbor
        if packet.is_link_up:
            self.graph.add_node(packet.source)
            self.graph.add_edge(edge, 1)
            if isinstance(source, HostEntity) and source not in list_of_hosts:
                list_of_hosts.append(source)
            self.port_lookup[source] = port
        else:
            # Nodes may become isolated in a router's graph after this
            self.graph.del_node(edge, 1)
            if isinstance(source,HostEntity) and source in list_of_hosts:
                del list_of_hosts,remove(source)
            try:
                del self.port_lookup[source]
            except KeyError as e:
                print "Why you remove %s when I DONT HAVE IT. QQ" % source
                print e

        # recompute forwarding table
            self._update_forwarding_table();
        # flood packet updates
            self._send_linkstate_update(packet); # Need to send link state update to all neighbors
    

    def _send_linkstate_update(packet, port=None):
        if isinstance(packet, DiscoveryPacket):
            # This clause only executes if a router is responding to a DiscoveryPacket
            # Creation of the LinkStatePacket occurs here
            packet_to_be_sent = LinkStatePacket(packet.src, self, packet.is_link_up)
        else: # packet arg is type LinkStatePacket
            packet_to_be sent = packet
        self.send(packet_to_be_sent, port, flood=True) # port's value is obtained from method header

    def _handle_linkstate_update(self, packet, port):
        # first, check for duplicate linkstate update
        if packet not in self.processed_packets:
            self.processed_packets.add(packet)

            # process update
            new_edge = edge(packet.node1, packet.node2)
            if packet.is_link_up:
                self.graphs.add_edge(new_edge, 1)
            else:
                self.graphs.del_edge(new_edge)

            # recompute forwarding table
            self._update_forwarding_table();

            # flood packet updates
            self._send_linkstate_update(packet, port) # Need to send link state update to all neighbors, except for neighbor that sent packet to current router

    def _update_forwarding_table():
        intermediate_dict = self.graphs.shortest_paths(self)
        self.forwarding_table = dict()
        for host in list_of_hosts:
            best_neighbor = intermediate_dict[host][0][0]
            self.forwarding_table[host] = best_neighbor

    def _handle_data(self, packet, port):
        destination = packet.dst
        try:
            best_neighbor = self.forwarding_table[destination]
            self.send(packet, port=self.port_lookup[best_neighbor.neighbor])        except KeyError as e:
            print "There is no route to this destination %s via this router, period." % destination
            print e


class LinkStatePacket (Packet):
    """
    A "link state packet" (Packet):
    Contains information on an edge and whether or not that edge
    went up or down. Sending out this packet is effectively
    equivalent to sending out a list of neighbors of a source packet A
    after a single link has gone up or down involving A.
    """

    def __init__(self, node1, node2, link_status):
        Packet.__init__(self)
        self.node1 = node1
        self.node2 = node2
        self.is_link_up = link_status
