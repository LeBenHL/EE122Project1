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

  def best_neighbor(self, destination, port_lookup):
    best_neighbor_so_far = None
    for neighbor, destinations_dict in self.iteritems():
      try:
        neighbor_cost = destinations_dict[destination]
        if best_neighbor_so_far is None or best_neighbor_so_far.cost > neighbor_cost or (best_neighbor_so_far.cost == neighbor_cost and port_lookup[best_neighbor_so_far.neighbor] > port_lookup[neighbor]):
          best_neighbor_so_far = Route(neighbor, destination, neighbor_cost)
      except KeyError as e:
        continue

    if best_neighbor_so_far:
      return best_neighbor_so_far
    else:
      raise NoRouteException()

  def process_neighbor(self, packet):
      source = packet.src
      distance_vector = packet.paths
      for host,cost in distance_vector.iteritems():
        self[source][host] = cost + 1

      unreachable_hosts = []
      for host in self[source].iterkeys():
        if not distance_vector.has_key(host):
          unreachable_hosts.append(host)
      
      for host in unreachable_hosts:
        del self[source][host]

'''
Create your RIP router in this file.
'''
class RIPRouter (Entity):
  def __init__(self):
    self.routing_table = RoutingTable()
    self.port_lookup = dict() # Dictionary with key=neighbor, value=corresponding port
    self.distance_vector = dict()
    self.prev_distance_vector = None

  def handle_rx (self, packet, port):
    if isinstance(packet, DiscoveryPacket):
      self._handle_discovery(packet, port)
    elif isinstance(packet, RoutingUpdate):
      self._handle_routing_update(packet, port)
    else:
      self._handle_data(packet, port)

  def _handle_discovery(self, packet, port):
    source = packet.src # source is another word for neighbor
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

    self._calculate_distance_vector()
    if (not self._equalDV()):
      # Need to send out different routing updates
      self._send_out_distance_vector(self.routing_table.iterkeys())
    elif packet.is_link_up:
      #Send only to the newly connected neighbor a DV ONLY IF LINK IS UP
      self._send_out_distance_vector([source])
      
  def _handle_routing_update(self, packet, port):
    self.routing_table.process_neighbor(packet)

    self._calculate_distance_vector()
    if (not self._equalDV()):
      # Need to send out different routing updates
      self._send_out_distance_vector(self.routing_table.iterkeys())

  # Return whether or not prev distance vector and current distance vector are the same (host, smallest cost)-wise
  def _equalDV(self):
    if (len(self.prev_distance_vector) != len(self.distance_vector)):
      return False
    # Here, both distance vectors have the same size
    for host, best_neighbor in self.distance_vector.iteritems():
      if (best_neighbor.cost != self.prev_distance_vector[host].cost):
        return False
    return True

  # Need to differentiate between neighbors and hosts??
  # Send to all neighbors their respective version of the distance vector
  def _send_out_distance_vector(self, neighbors):

    # Each iteration sends out one distance vector  
    for neighbor in neighbors:
      real_distance_vector = dict()
      for host, best_neighbor in self.distance_vector.iteritems():
        if (best_neighbor.neighbor != neighbor): # Takes into account Poison Reverse
          real_distance_vector[host] = best_neighbor.cost
      routing_update_packet = RoutingUpdate()
      routing_update_packet.paths = real_distance_vector
      print real_distance_vector, self, neighbor
      self.send(routing_update_packet, port=self.port_lookup[neighbor])
    
  def _calculate_distance_vector(self):
    self.prev_distance_vector = self.distance_vector
    self.distance_vector = dict()

    # for loop scans routing_table for all possible hosts
    for neighbor, host_dict in self.routing_table.iteritems():
      for host in host_dict.iterkeys():
        if not self.distance_vector.has_key(host):
          self.distance_vector[host] = self.routing_table.best_neighbor(host, self.port_lookup)

              
  def _handle_data(self, packet, port):
    destination = packet.dst
    try:
      best_neighbor = self.distance_vector[destination]
      self.send(packet, port=self.port_lookup[best_neighbor.neighbor])
    except KeyError as e:
      print "There is no route to this destination %s via this router, period." % destination
      print e


