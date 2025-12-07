# Note: fixed could possibly be merged with blacklist; only difficulty is blacklist is edge-wise and fixed is node-wise
# Note: I should probably find a better word than "fixed", I was thinking "sources", but I already use that to mean AND nodes with no prereqs


import copy
import random
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
                reachable[node_key] = True
                add_node(node)

            for prereq in node["prereqs"]:
                if graph_utils.make_edge_key(prereq, node) in blacklist:
                    blacklisted_and_nodes[node_key] = True
                    break
        
        if fixed_truthy(node_key):
            reachable[node_key] = True
            add_node(node)
    

    # Now, do updates
    while curr_ind < len(open):
        curr_node = open[curr_ind]
        
        for dependent in curr_node["dependents"]:
            dependent_key = graph_utils.make_key(dependent)
            dependent_node = graph[dependent_key]
            num_satisfiers[dependent_key] += 1


            if dependent_node["op"] == "and":
                if len(dependent_node["prereqs"]) == num_satisfiers[dependent_key]:
                    reachable[dependent_key] = True

                    # If this is not a blacklisted AND node, propagate
                    if not dependent_key in blacklisted_and_nodes:
                        add_node(dependent_node)
            elif dependent_node["op"] == "or":
                reachable[dependent_key] = True

                # If this wasn't already added to open and this edge is not blacklisted, propagate
                if not dependent_key in in_open and not graph_utils.make_edge_key(curr_node, dependent) in blacklist:
                    add_node(dependent_node)
        
        curr_ind += 1
    

    return {"sorted": open, "reachable": reachable}


# Try finding a path through the graph using sort
# Assume once a fixed node has been toggled, it will stay toggled, and then it just needs to be reached once
# Wait, this isn't true of rooms?
# We somehow need a way of setting a specific room as the starting room (maybe add/remove to fixed)
def traverse_monotonic(graph, blacklist=None, fixed=None):
    if fixed is None:
        fixed = {}
        

    # This part makes some heavy assumptions about how things are structured and has "location"-ness baked in
    # TODO: Refactor!
    # Also delete the start to start room connection, at least for now
    starting_room = None
    fixed_to_room = {}
    for node_name, node in graph.items():
        if node["type"] == "start":
            start_loc_ind = None
            for ind, dependent in enumerate(node["dependents"]):
                if dependent["type"] == "location":
                    start_loc_ind = ind
                    starting_room = graph_utils.make_key(dependent)
                    break
            del node["dependents"][start_loc_ind]
            starting_room_node = graph[starting_room]
            ind_to_del = None
            for ind, prereq in enumerate(starting_room_node["prereqs"]):
                if prereq["type"] == "start":
                    ind_to_del = ind
                    break
            del starting_room_node["prereqs"][ind_to_del]
        if node_name in fixed:
            for prereq in node["prereqs"]:
                if prereq["type"] == "location":
                    fixed_to_room[node_name] = graph_utils.make_key(prereq)
                    break


    curr_room = starting_room
    ability_order = []
    while True:
        fixed[curr_room] = True
        local_sort_info = sort(graph, blacklist, fixed)
        del fixed[curr_room]

        local_sort_rooms = []
        for node in local_sort_info["sorted"]:
            if node["type"] == "location":
                local_sort_rooms.append(node)

        reachable_fixed = []
        for node_name in fixed:
            if fixed[node_name] is False and node_name in local_sort_info["reachable"]:
                reachable_fixed.append(node_name)
        next_node_name = random.choice(reachable_fixed)
        ability_order.append(next_node_name)
        fixed[next_node_name] = True
        curr_room = fixed_to_room[next_node_name]

        all_fixed_found = True
        for val in fixed.values():
            if val is False:
                all_fixed_found = False
        if all_fixed_found:
            break
    

    return ability_order