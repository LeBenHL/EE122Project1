from rip_router import Graph

graph = Graph()
graph.add_node("h1a")
graph.add_node("h1b")
graph.add_node("h2a")
graph.add_node("h2b")
graph.add_node("s1")
graph.add_node("s2")
graph.add_node("s3")
graph.add_node("s4")
graph.add_node("s5")

graph.add_edge(("h1a", "s1"), 2)
graph.add_edge(("h1b", "s1"), 3)
graph.add_edge(("s1", "s3"), 5)
graph.add_edge(("s1", "s4"), 4)
graph.add_edge(("s4", "s5"), 1)
graph.add_edge(("s3", "s2"), 3)
graph.add_edge(("s5", "s2"), 2)
graph.add_edge(("s2", "h2a"), 3)
graph.add_edge(("s2", "h2b"), 1)