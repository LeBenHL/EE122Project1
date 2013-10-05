import sim
from sim.core import CreateEntity, topoOf
from sim.basics import BasicHost
from hub import Hub
import sim.topo as topo

def create(switch_type = Hub, host_type = BasicHost):
  switch_type.create('s1')
  switch_type.create('s2')
  switch_type.create('s3')
  switch_type.create('s4')
  switch_type.create('s5')
  switch_type.create('s6')
  switch_type.create('s7')

  host_type.create('h1a')
  host_type.create('h2a')

  topo.link(s1, h1a)
  topo.link(s7, h2a)

  topo.link(s1, s2)
  topo.link(s1, s3)
  topo.link(s1, s4)
  topo.link(s1, s5)
  topo.link(s1, s6)

  topo.link(s7, s2)
  topo.link(s7, s3)
  topo.link(s7, s4)
  topo.link(s7, s5)
  topo.link(s7, s6)
