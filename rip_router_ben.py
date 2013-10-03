from sim.api import *
from sim.basics import *

from collections import namedtuple
import operator

Route = namedtuple('Route', ['via', 'cost'], verbose=False)

class RoutingTable(dict):

  def __init__(self, *args):
    dict.__init__(self, args)
    self.neighbor_to_port_map = dict()

  def add_link(self, source, port, cost):
    self.add_or_update_path(source, source, cost);
    self.neighbor_to_port_map[source] = port

  def remove_link(self, source):
    #Remove all entries in routing table in which we use the unlinked router
    destinations = []
    for destination, vias in self.iteritems():
      if vias.has_key(source):
        destinations.append(destination)
    for destination in destinations:
      self.destroy_path(destination, source)

    del self.neighbor_to_port_map[source]  

  def add_or_update_path(self, destination, via, cost):
    try:
      if not self.has_key(destination):
        self[destination] = dict()
      self[destination][via] = cost
    except KeyError as e:
      print "Something bad happened when trying to set %s via %s" % (destination, via)
      print e

  def destroy_path(self, destination, via):
    try:
      del self[destination][via]
      if len(self[destination]) == 0:
        del self[destination]
    except KeyError as e:
      print "Why are you trying to destroy %s via %s when it doesn't exist?" % (destination, via)
      print e

  def best_routes(self):
    best_routes = dict()
    for destination, vias in self.iteritems():
      best_route = None
      for (via, cost) in vias.iteritems():
        if best_route is None or best_route.cost > cost or (best_route.cost == cost and self.neighbor_to_port_map[best_route.via] > self.neighbor_to_port_map[via]):
          best_route = Route(via, cost)

      assert best_route != None
      best_routes[destination] = best_route

    return best_routes

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):

    def __init__(self):
      self.best_routes = dict()
      self.routing_table = RoutingTable()

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
        self.routing_table.add_link(source, port, 1)
      else:
        self.routing_table.remove_link(source)

      self.calculate_best_routes()

    def handle_routing_update(self, packet, port):
      source = packet.src
      source_cost = self.get_cost(source)

      #Find all previous destinations we can get to via the source
      previous_destinations_via_source = []
      for destination, vias in self.routing_table.iteritems():
        if vias.has_key(source):
          previous_destinations_via_source.append(destination)

      #Kind of Hacky. Since we are getting an update from the source, we know it is right next to us
      #So we want to remove the source from the list so we don't accidently remove the path because
      #of the implicit withdrawal
      previous_destinations_via_source.remove(source)

      for destination, cost in packet.paths.iteritems():
        self.routing_table.add_or_update_path(destination, source, cost + source_cost)
        try:
          previous_destinations_via_source.remove(destination)
        except ValueError:
          #It's ok if we can't remove it! This means we found a destination we couldn't get to before!
          pass

      #Delte all paths that were not updated
      for destination in previous_destinations_via_source:
        self.routing_table.destroy_path(destination, source)

      self.calculate_best_routes()

    def handle_data_packet(self, packet, port):
      print self
      destination = packet.dst
      if self == destination:
        self.handle_packet_arrived(packet)
      else:
        try:
          route = self.best_routes[destination]
          self.send(packet, self.routing_table.neighbor_to_port_map[route.via])
        except KeyError as e:
          print "I DIDN'T KNOW WHAT TO DO TO GET TO %s" % destination
          print e

    def handle_packet_arrived(self, packet):
      print packet.trace

    def get_cost(self, destination):
      try:
        return self.best_routes[destination].cost
      except KeyError as e:
        print "I DIDN'T KNOW WHAT TO DO TO GET TO %s" % destination
        print e

    def calculate_best_routes(self):
      previous_best_routes = self.best_routes.copy()
      self.best_routes = self.routing_table.best_routes()

      if len(set(previous_best_routes.items()) ^ set(self.best_routes.items())) > 0:
        self.send_routing_update()

    def send_routing_update(self):
      update = RoutingUpdate()
      base_paths = dict()
      for destination, route in self.best_routes.iteritems():
        base_paths[destination] =  route.cost

      for neighbor, port in self.routing_table.neighbor_to_port_map.iteritems():
        #POISON REVERSE! DON'T ADVERTISE DESTINATIONS TO MY NEIGHBOR IF I AM USING THEM TO SEND TO MY DESTINATION
        paths = base_paths.copy()
        for destination, (via, cost) in self.best_routes.iteritems():
          if via == neighbor:
            del paths[destination]
        update.paths = paths
        self.send(update, port)



