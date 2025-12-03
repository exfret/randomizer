import json
import graphlib.graph_utils as graph_utils
import graphlib.top_sort.sort_with_blacklist as top_sort
import randomization.prereq_shuffle as shuffle

node_list = None
with open("data/metroid-planets.json", "r") as file:
    node_list = json.load(file)

graph = {}
for node_class in node_list.values():
    for node in node_class.values():
        graph[graph_utils.make_key(node)] = node

edges_to_shuffle = {}
for node in graph.values():
    num_loc_prereqs = 0
    for prereq in node["prereqs"]:
            if prereq["type"] == "location" and node["type"] == "items":
                 num_loc_prereqs += 1
    if num_loc_prereqs == 1:
        # TODO: Make this work for items in multiple locations too!
        for prereq in node["prereqs"]:
            if prereq["type"] == "location" and node["type"] == "items":
                # Let the first place an item appears be its canonical place
                # This is just because items are OR nodes and prereq shuffle is technically for AND nodes; might not be necessary to do this, though
                edges_to_shuffle[graph_utils.make_edge_key(prereq, node)] = True
                break

deps_with_new_prereqs = shuffle.prereq_shuffle(graph, edges_to_shuffle)

for item_key, locs in deps_with_new_prereqs.items():
    padded_name = graph[item_key]["name"]
    padding = 18 - len(padded_name)
    for i in range(padding):
        padded_name += " "
    print(padded_name + "--> \t" + locs[0]["name"].split("Pickup")[-1][2:-12])

# TODO: Need to fix dependents too!
for dep_name, prereqs in deps_with_new_prereqs.items():
    node = graph[dep_name]
    graph[dep_name]["prereqs"] = prereqs
sort_info = top_sort.sort(graph)

for node in sort_info["sorted"]:
    if graph_utils.make_key(node) in deps_with_new_prereqs:
        print(node["name"])