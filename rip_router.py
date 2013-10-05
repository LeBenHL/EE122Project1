from sim.api import *
from sim.basics import *

import heapq
from collections import namedtuple

Route = namedtuple("Route", ["neighbor", "host", "cost"])

class NoRouteException(Exception):
  pass

class RoutingTable(dict):

  def __init__(self, *args):
    dict.__init__(self, args)
    self.cost_lookup = dict()

  def add_neighbor(self, source, cost=1):
    if self.has_key(source):
      #Look up old cost, find delta and apply it
      delta = cost - self.cost_lookup[source]
      for host in self[source].iterkeys():
        self[source][host] += delta
    else:
      self[source] = dict()
      if isinstance(source, HostEntity):
        self[source][source] = cost

    self.cost_lookup[source] = cost


  def remove_neighbor(self, source):
    try:
      del self[source]
      del self.cost_lookup[source]
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
        self[source][host] = cost + self.cost_lookup[source]

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

  count = 0

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
      RIPRouter.count += 1
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

'''
EC2
'''
class SmartRIPRouter (RIPRouter):

  def _handle_discovery(self, packet, port):
    source = packet.src # source is another word for neighbor
    if packet.is_link_up:
      self.routing_table.add_neighbor(source, packet.latency)
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

'''
EC3
'''
class Graph:

  def __init__(self):
    self.adjaceny_list = dict()
    self.edge_costs = dict()

  def add_node(self, node):
    self.adjaceny_list[node] = set()

  def add_edge(self, edge, wt=1):
    node1 = edge[0]
    node2 = edge[1]
    try:
      self.adjaceny_list[node1].add(node2)
      self.adjaceny_list[node2].add(node1)
      self._add_edge_weight(edge, wt)
    except KeyError as e:
      print "Cannot add edge (%s, %s). Because one or more nodes don't exist" % (node1, node2)
      print e

  def _add_edge_weight(self, edge, wt):
    reverse_edge = (edge[1], edge[0])
    self.edge_costs[reverse_edge] = wt
    self.edge_costs[edge] = wt

  def del_edge(self, edge):
    node1 = edge[0]
    node2 = edge[1]
    try:
      self.adjaceny_list[node1].remove(node2)
      self.adjaceny_list[node2].remove(node1)
      self._remove_edge_weight(edge)
    except KeyError as e:
      print "Cannot delete edge (%s, %s). Because one or more nodes don't exist" % (node1, node2)
      print e

  def _remove_edge_weight(self, edge):
    reverse_edge = (edge[1], edge[0])
    del self.edge_costs[reverse_edge]
    del self.edge_costs[edge] 

  def del_node(self, node):
    try:
      for other_node in self.adjaceny_list[node]:
        self.adjaceny_list[other_node].remove(node)
        self._remove_edge_weight((node, other_node))
      del self.adjaceny_list[node]
    except KeyError:
      print "Something bad happened when deleting %s" % node

  def nodes(self):
    return self.adjaceny_list.keys()

  def neighbors(self, node):
    neighbors = []
    for other_node in self.adjaceny_list[node]:
      neighbors.append((other_node, self.edge_costs[(node, other_node)]))
    return neighbors

  """
  Returns a dict of (node, (prev, cost)) pairs using dijkstras algorithm from some node
  """
  def shortest_paths(self, node):
    dist = []
    heapitems = dict()
    previous = dict()
    via = dict()
    shortest_paths = dict()
    for n in self.nodes():
      item = [float('inf'), n]
      heapq.heappush(dist, item)
      previous[n] = None
      via[n] = None
      heapitems[n] = item

    heapitems[node][0] = 0
    heapq._siftdown(dist, 0, dist.index(heapitems[node]))

    while dist:
      cost, n = heapq.heappop(dist) 
      if cost == float('inf'):
        break
      shortest_paths[n] = (via[n], cost)

      for neighbor, edge_cost in self.neighbors(n):
        alt = cost + edge_cost
        if alt < heapitems[neighbor][0]:
          heapitems[neighbor][0] = alt
          previous[neighbor] = n
          heapq._siftdown(dist, 0, dist.index(heapitems[neighbor]))

          if n == node:
            via[neighbor] = neighbor
          else:
            via[neighbor] = via[n]

    return shortest_paths



    





