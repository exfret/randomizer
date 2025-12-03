# Note: fixed could possibly be merged with blacklist; only difficulty is blacklist is edge-wise and fixed is node-wise
# Note: I should probably find a better word than "fixed", I was thinking "sources", but I already use that to mean AND nodes with no prereqs


import copy
import graphlib.graph_utils as graph_utils


def sort(graph, blacklist=None, fixed=None):
    if blacklist is None:
        blacklist = {}
    else:
        # Deepcopy blacklist since we modify it and don't want those modifications to carry upstream
        # This is inefficient but fine for now
        blacklist = copy.deepcopy(blacklist)
    
    # fixed[node_name] == True if node is set to always emit reachable, fixed[node_name] == False if always emit nonreachable
    if fixed is None:
        fixed = {}
    def fixed_falsey(node_name):
        return node_name in fixed and fixed[node_name] is False
    def fixed_truthy(node_name):
        return node_name in fixed and fixed[node_name] is True


    open = []
    in_open = {}
    # Things immediately reachable from in_open, even allowing blacklisted edges
    reachable = {}
    # Keep track of AND nodes that have at least one blacklisted connection
    blacklisted_and_nodes = {}
    num_satisfiers = {}
    curr_ind = 0


    def add_node(node):
        node_key = graph_utils.make_key(node)
        open.append(node)
        in_open[node_key] = True
    

    # Being fixed_falsey is essentially the same as having all prerequisites blacklisted
    # The only special case is AND nodes with no prerequisites, which is handled when sources are added
    for node_name in fixed:
        if fixed[node_name] is False:
            node = graph[node_name]
            for prereq in node["prereqs"]:
                blacklist[graph_utils.make_edge_key(prereq, node)] = True


    # Add sources and populate blacklisted_and_nodes
    for node_key, node in graph.items():
        num_satisfiers[node_key] = 0

        if node["op"] == "and":
            if len(node["prereqs"]) == 0 and not fixed_falsey(node_key):
                add_node(node)

            for prereq in node["prereqs"]:
                if graph_utils.make_edge_key(prereq, node) in blacklist:
                    blacklisted_and_nodes[node_key] = True
                    break
        
        if fixed_truthy(node_key):
            add_node(node)
    

    # Now, do updates
    while curr_ind < len(open):
        curr_node = open[curr_ind]
        
        for dependent in curr_node["dependents"]:
            dependent_key = graph_utils.make_key(dependent)
            dependent_node = graph[dependent_key]
            num_satisfiers[dependent_key] += 1


            if dependent["op"] == "and":
                if len(dependent_node["prereqs"]) == num_satisfiers[dependent_key]:
                    reachable[dependent_key] = True

                    # If this is not a blacklisted AND node, propagate
                    if not dependent_key in blacklisted_and_nodes:
                        add_node(dependent_node)
            elif dependent["op"] == "or":
                reachable[dependent_key] = True

                # If this wasn't already added to open and this edge is not blacklisted, propagate
                if not dependent_key in in_open and not graph_utils.make_edge_key(curr_node, dependent) in blacklist:
                    add_node(dependent_node)
        
        curr_ind += 1
    

    return {"sorted": open, "reachable": reachable}