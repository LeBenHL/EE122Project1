from sim.api import *
from sim.basics import *

import operator

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
    def __init__(self):
      self.best_routes = dict()
      self.routing_table = dict()
      self.neighbor_to_port_map = dict()

    def handle_rx (self, packet, port):
      # Check for Type of packet
      if isinstance(packet, DiscoveryPacket):
        self.handle_discovery_packet(packet, port)
      elif isinstance(packet, RoutingUpdate):
        self.handle_routing_update(packet, port)
      else:
        self.handle_data_packet(packet, port)

    def handle_discovery_packet(self, packet, port):
      source = packet.src
      if packet.is_link_up:
        self.add_or_update_path(source, source, 1)
        self.neighbor_to_port_map[source] = port
      else:
        self.destroy_path(source, source)
        del self.neighbor_to_port_map[source]

      self.calculate_best_routes()

    def handle_routing_update(self, packet, port):
      source = packet.src
      source_cost = self.get_cost(source)
      for destination, cost in packet.paths.iteritems():
        self.add_or_update_path(destination, source, cost + source_cost)

      self.calculate_best_routes()

    def handle_data_packet(self, packet, port):
      destination = packet.dst
      if self == destination:
        self.handle_packet_arrived(packet)
      try:
        via, cost = self.best_routes[destination]
        self.send(packet, self.neighbor_to_port_map[via])
      except KeyError as e:
        print "I DIDN'T KNOW WHAT TO DO TO GET TO %s" % destination
        print e

    def hand_packet_arrived(self, packet):
      print packet.trace

    def get_cost(self, destination):
      try:
        return self.best_routes[destination][1]
      except KeyError as e:
        print "I DIDN'T KNOW WHAT TO DO TO GET TO %s" % destination
        print e

    def add_or_update_path(self, destination, via, cost):
      try:
        if not self.routing_table.has_key(destination):
          self.routing_table[destination] = dict()
        self.routing_table[destination][via] = cost
      except KeyError as e:
        print "Something bad happened when trying to set %s via %s" % (destination, via)
        print e

    def destroy_path(self, destination, via):
      try:
        del self.routing_table[destination][via]
        if len(self.routing_table[destination]) == 0:
          del self.routing_table[destination]
      except KeyError as e:
        print "Why are you trying to destroy %s via %s when it doesn't exist?" % (destination, via)
        print e

    def calculate_best_routes(self):
      previous_best_routes = self.best_routes.copy()
      print previous_best_routes
      best_routes = dict()
      for destination, vias in self.routing_table.iteritems():
        via, cost = min(vias.iteritems(), key=operator.itemgetter(1))
        best_routes[destination] = (via, cost)
      print previous_best_routes
      print best_routes
      print

      self.best_routes = best_routes

      routing_update = False
      if len(previous_best_routes) == len(best_routes):
        for destination, via in previous_best_routes.iteritems():
          try:
            print best_routes[destination]
            print via
            if not best_routes[destination] == via:
              routing_update = True
              break
          except:
            routing_update = True
            break
      else:
        routing_update = True

      if routing_update:
        self.send_routing_update()

    def send_routing_update(self):
      update = RoutingUpdate()
      for destination, via in self.best_routes.iteritems():
        update.add_destination(destination, via[1])

      ports = []
      for neighbor, port in self.neighbor_to_port_map.iteritems():
        self.send(update, port)



