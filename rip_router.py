from sim.api import *
from sim.basics import *

from collections import namedtuple

Route = namedtuple("Route", ["neighbor", "host", "cost"])

class NoRouteException(Exception):
  pass

class RoutingTable(dict):

  def __init__(self, *args):
    dict.__init__(self, args)

  def add_neighbor(self, source):
    self[source] = dict()
    if isinstance(source, HostEntity):
      self[source][source] = 1

  def remove_neighbor(self, source):
    try:
      del self[source]
    except KeyError as e:
      print "Why you remove %s when I DONT HAVE IT. QQ" % source
      print e

  def best_neighbor(destination, port_lookup):
    best_neighbor_so_far = None
    for neighbor, destinations_dict in self.iteritems():
      try:
        neighbor_cost = destinations_dict[destination]
        if best_neighbor is None or best_neighbor_so_far.cost > neighbor_cost or (best_neighbor_so_far.cost == neighbor_cost and (port_lookup[best_neighbor_so_far.neighbor] > port_lookup[neighbor]):
          best_neighbor_so_far = Route(neighbor, destination, neighbor_cost)
      except KeyError as e:
        continue

    if best_neighbor_so_far:
      return best_neighbor_so_far.neighbor
    else:
      raise NoRouteException()

  # First, 
  def process_neighbor(self, packet):
      source = packet.src
      distance_vector = packet.paths
      for host,cost in distance_vector.iteritems():
        self[source][host] = cost + 1

      unnreachable_hosts = []
      for host in self[source].iterkeys():
        if not distance_vector.has_key(host)
          unnreachable_hosts.append(host)
      
      for host in unnreachable_hosts:
        del self[source][host]

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
  def __init__(self):
    self.routing_table = RoutingTable()
    self.port_lookup = dict()
    self.distance_vector = dict()

  def handle_rx (self, packet, port):
    if isinstance(packet, DiscoveryPacket):
      _handle_discovery(packet, port)
    elif isinstance(packet, RoutingUpdate):
      _handle_routing_update(packet, port)
    else:
      _handle_data(packet, port)

  def _handle_discovery(self, packet, port):
    source = packet.src
    if packet.is_link_up:
      self.routing_table.add_neighbor(source)
      self.port_lookup[source] = port
    else:
      #LINK IS DOWN. QQ
      self.routing_table.remove_neighbor(source)
      try:
        del self.port_lookup[source]
      except KeyError as e:
        print "Why you remove %s when I DONT HAVE IT. QQ" % source
        print e
      
  def _handle_routing_update(self, packet, port):
    self.routing_table.process_neighbor(packet)
    if (self._update_distance_vector()):
      routing_update_packet = RoutingUpdate()
      routing_update_packet.paths = distance_vector
      self.send(routing_update_packet, port=None, flood=True)

  # This will update the distance vector if it needs changes
  # and returns a boolean depending on whether or not DV was changed 
  def _update_distance_vector():
    pass

  def _handle_data(packet, port):
    destination = packet.dst
    try:
      best_neighbor = self.routing_table.best_neighbor(destination, self.port_lookup)
      self.send(packet, port=self.port_lookup[best_neighbor])
    except NoRouteException as e:
      print "There is no route to this destination %s via this router, period." % destination
      print e

  def _create_packet_update():


