from copy import deepcopy
import math
import networkx as nx
import pydot


def copy_dict_and_remove_name(dd):
    ddc = deepcopy(dd)
    del ddc['name']
    return ddc

def data_to_graph(style, relations):
    """
    style - yaml
    relations - pandas dataframe
    """
    g = nx.DiGraph()
    
    node_data = {
        entity['name'] : copy_dict_and_remove_name(entity)
        for entity in style['entities']
    }

    # can probably rewrite with more succinct NX call?

    for relation in relations.iterrows():
        nsubject = relation[1]['subject']
        nobject = relation[1]['object']
        
        if nsubject not in g.nodes() and nsubject in node_data:
            g.add_node(nsubject, **node_data[nsubject])
        
        if nobject not in g.nodes() and nobject in node_data:
            g.add_node(nobject, **node_data[nobject])

        g.add_edge(
            nsubject, # will be lower case _s_ubject later, etc.
            nobject,
            verb = relation[1]['verb'],
            context = relation[1]['context']
        )
            
    return g

def graphviz_lookup(typ, style):
    # this can be optimized for constant time lookup with a preprocessing step
    for etyp in style['entity-types']:
        match = False
        if etyp['name'] == typ:
            match = True
            return etyp['graphviz']
        
        gv_attr = etyp['graphviz'].copy()
        
        if 'subtypes' in etyp:
            for estyp in etyp['subtypes']:
                if estyp['name'] == typ:
                    match = True

                    if 'graphviz' in estyp:
                        s_gv_attr = estyp['graphviz'].copy()
                        gv_attr.update(s_gv_attr)

        if match:
            return gv_attr

    return {}


def imho_graph_to_dot(imhog, style, layout="dot"):
    dot = pydot.Dot()
    
    # arbitrary, should be configurable
    dot.set('layout', layout)
    dot.set('rankdir', 'TB')                                                    
    dot.set('concentrate', True)                                                
    dot.set_node_defaults(shape='record')
    
    for uid, dat in imhog.nodes(data=True):
        node = pydot.Node(
                uid,
                #label = dat['long_name']
        )

        if 'type' in dat:
            gv_attr = graphviz_lookup(dat['type'], style)
        else:
            gv_attr = {}
        
        for attr in gv_attr:
            node.set(attr, gv_attr[attr])

        dot.add_node(node)

    edges = list(imhog.edges(data=True))

    clusters = {}

    for edge in edges:
        context = edge[2]['context']
    
        if context not in clusters:
            clusters[context] = []
    
        clusters[context].append(edge)
        
    for context in clusters:
        if not isinstance(context, str) and math.isnan(context):
            g = dot
        else:
            cluster = pydot.Cluster(graph_name = context, label = context)
            dot.add_subgraph(cluster)
            g = cluster

        for edge in clusters[context]:
            g.add_edge(
                pydot.Edge(
                    edge[0],
                    edge[1],
                    label = edge[2]['verb']
                ))

    for n in dot.get_nodes():
        # Change the style of all nodes
        #n.set('style', 'filled')
        #n.set('fillcolor', 'aliceblue')
        n.set('fontsize', '10')
        n.set('fontname', 'Trebuchet MS, Tahoma, Verdana, Arial, Helvetica, sans-serif')

    return dot
