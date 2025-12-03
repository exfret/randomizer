import random
import graphlib.top_sort.sort_with_blacklist as top_sort
import graphlib.graph_utils as graph_utils


# Currently just works if dependents are AND nodes
def prereq_shuffle(graph, edges_to_shuffle):
    is_dep = {}
    for edge_key in edges_to_shuffle:
        # end node of edge is a dependent
        is_dep[edge_key[1]] = True


    init_sort = top_sort.sort(graph)

    
    deps_sorted = []
    prereqs_shuffled = []
    dep_to_shuffled_inds = {}
    blacklist = {}
    for node in init_sort["sorted"]:
        node_key = graph_utils.make_key(node)

        if node_key in is_dep:
            deps_sorted.append(node)
            dep_to_shuffled_inds[node_key] = []

            for prereq_ind, prereq in enumerate(node["prereqs"]):
                if graph_utils.make_edge_key(prereq, node) in edges_to_shuffle:
                    prereqs_shuffled.append(prereq)
                    dep_to_shuffled_inds[node_key].append(prereq_ind)
                    blacklist[graph_utils.make_edge_key(prereq, node)] = True
    

    random.shuffle(prereqs_shuffled)


    final_sort = top_sort.sort(graph, blacklist)


    inds_used = {}
    dep_to_new_prereqs = {}
    for dep in deps_sorted:
        dep_key = graph_utils.make_key(dep)
        dep_to_new_prereqs[dep_key] = []


        # Search for new prerequisites
        used_prereqs = {}
        for i in range(len(dep_to_shuffled_inds[dep_key])):
            for ind, prereq in enumerate(prereqs_shuffled):
                prereq_key = graph_utils.make_key(prereq)

                # Check that this prereq hasn't been used yet by another dependent
                if not ind in inds_used:
                    # Check that this prereq is reachable
                    if prereq_key in final_sort["reachable"]:
                        # Check that we haven't connected this same prereq to this dependent already
                        if not prereq_key in used_prereqs:
                            # Add this prereq
                            inds_used[ind] = True
                            dep_to_new_prereqs[dep_key].append(prereq)
                            used_prereqs[prereq_key] = True
                            break
        
        # Assert we found enough prereqs
        assert(len(dep_to_new_prereqs[dep_key]) == len(dep_to_shuffled_inds[dep_key]))


        # Remove dep from blacklist and find new reachable prereqs
        for prereq in dep["prereqs"]:
            if graph_utils.make_edge_key(prereq, dep) in edges_to_shuffle:
                del blacklist[graph_utils.make_edge_key(prereq, dep)]

        final_sort = top_sort.sort(graph, blacklist)
    

    # Fix dependent prereqs
    deps_with_new_prereqs = {}
    for dep in deps_sorted:
        dep_key = graph_utils.make_key(dep)
        deps_with_new_prereqs[dep_key] = []

        for prereq_ind, prereq in enumerate(dep["prereqs"]):
            if prereq_ind in dep_to_shuffled_inds[dep_key]:
                modified_prereq_ind = list.index(dep_to_shuffled_inds[dep_key], prereq_ind)
                deps_with_new_prereqs[dep_key].append(dep_to_new_prereqs[dep_key][modified_prereq_ind])
    

    return deps_with_new_prereqs