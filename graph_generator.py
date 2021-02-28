import networkx as nx
from geopy.distance import geodesic
import random
import numpy as np
import argparse


# def generate_graph(file):
    # G = nx.Graph()
    # G.add_node(0, cpu=3, memory=10.0, bandwidth=1000.0)
    # G.add_node(1, cpu=3, memory=25.0, bandwidth=1000.0)
    # G.add_node(2, cpu=10, memory=50.0, bandwidth=1000.0)
    # G.add_node(3, cpu=1, memory=10.0, bandwidth=1000.0)
    # G.add_node(4, cpu=3, memory=30.0, bandwidth=1000.0)
    # G.add_edge(0, 2, latency=50.0)
    # G.add_edge(1, 2, latency=50.0)
    # G.add_edge(2, 3, latency=50.0)
    # G.add_edge(2, 4, latency=50.0)

    # nx.write_gpickle(G, file)
def generate_fatTree_graph(k, file):
    G = nx.Graph()
    servers = int(pow(k, 3) / 4)
    edge_sw = int(k * (k / 2))
    agg_sw = int(k * (k / 2))
    core_sw = int(pow(k / 2, 2))
    gw = 1
    edge_devices = 300
    sv_idx_range = range(0, servers)
    last_sv_idx = sv_idx_range[-1]
    edge_idx_range = range(last_sv_idx + 1, last_sv_idx + 1 + edge_sw)
    last_edge_idx = edge_idx_range[-1]
    agg_idx_range = range(last_edge_idx + 1, last_edge_idx +1 +agg_sw)
    last_agg_idx = agg_idx_range[-1]
    core_idx_range = range(last_agg_idx + 1, last_agg_idx + 1 + core_sw)
    last_core_idx = core_idx_range[-1]
    gw_idx = last_core_idx + 1
    edge_dev_idx_range = range(gw_idx + 1, gw_idx + 1 + edge_devices)
    last_edge_dev_idx = edge_dev_idx_range[-1]
    # generate nodes
    for i in range(0, last_edge_dev_idx + 1):
        G.add_node(i, cpu=100, memory=100.0, bandwidth=1000.0)

    # add link between host and edge sw
    sv_cluster = -1
    for i in sv_idx_range:
        if i % int(k / 2) == 0:
            sv_cluster += 1

        G.add_edge(i, edge_idx_range[0] + sv_cluster, latency=50.0)

    # add link between edge sw and agg sw
    pod = -int(k / 2)
    for i in edge_idx_range:
        if i % int(k / 2) == 0:
            pod += int(k / 2)
        for j in range(0, int(k / 2)):
            G.add_edge(i, agg_idx_range[0] + j + pod, latency=50.0)

    # add link between agg sw and core sw
    for i in agg_idx_range:
        for j in range(int(k / 2) - 1):
            if i % int(k / 2) == j:
                for m in range(core_idx_range[j * int(k / 2)], core_idx_range[(j + 1) * int(k / 2)]):
                    G.add_edge(i, m, latency=50.0)

        if i % int(k / 2) == (int(k / 2) - 1):
            for m in range(core_idx_range[(int(k / 2) - 1) * int(k / 2)], core_idx_range[-1] + 1):
                G.add_edge(i, m, latency=50.0)

    # add link between core sw and gw
    for i in core_idx_range:
        G.add_edge(i, gw_idx, latency=50.0)

    # add link between gw and edge devices
    for i in edge_dev_idx_range:
        G.add_edge(i, gw_idx, latency=50.0)

    nx.write_gpickle(G, file)

def gml_reader(seed, cpu, memory, bandwidth, inputfile, outputfile):
    SPEED_OF_LIGHT = 299792458  # meter per second
    PROPAGATION_FACTOR = 0.77  # https://en.wikipedia.org/wiki/Propagation_delay

    random.seed(seed)

    file = inputfile
    if not file.endswith(".gml"):
        raise ValueError("{} is not a GraphML file".format(file))
    network = nx.read_gml(file)

    # TODO assume undirected graph??
    newnetwork = nx.Graph()
    mapping = dict()

    for num, node in enumerate(network.nodes()):
        mapping[node] = num
        newnetwork.add_node(num, cpu=random.randint(
            *cpu), memory=float(random.uniform(*memory)), bandwidth=float(random.uniform(*bandwidth)))

    for e in network.edges():
        n1 = network.nodes(data=True)[e[0]]
        n2 = network.nodes(data=True)[e[1]]
        n1_coord = np.array((n1['graphics'].get("x"), n1['graphics'].get("y")))
        n2_coord = np.array((n2['graphics'].get("x"), n2['graphics'].get("y")))

        distance = np.linalg.norm(n1_coord-n2_coord)
        distance = distance/0.00062137  # miles->meter
        delay = (distance / SPEED_OF_LIGHT * 1000) * \
            PROPAGATION_FACTOR  # in milliseconds

        newnetwork.add_edge(mapping[e[0]], mapping[e[1]], latency=float(delay))

    nx.write_gpickle(newnetwork, outputfile)


def graphml_reader(seed, cpu, memory, bandwidth, inputfile, outputfile):
    SPEED_OF_LIGHT = 299792458  # meter per second
    PROPAGATION_FACTOR = 0.77  # https://en.wikipedia.org/wiki/Propagation_delay

    random.seed(seed)
    # setting ranged for random values of the nodes

    file = inputfile
    if not file.endswith(".graphml"):
        raise ValueError("{} is not a GraphML file".format(file))
    network = nx.read_graphml(file, node_type=int)

    # TODO assume undirected graph??
    newnetwork = nx.Graph()
    mapping = dict()

    for num, node in enumerate(network.nodes()):
        mapping[node] = num
        newnetwork.add_node(num, cpu=random.randint(
            *cpu), memory=float(random.uniform(*memory)), bandwidth=float(random.uniform(*bandwidth)))

    for e in network.edges():
        n1 = network.nodes(data=True)[e[0]]
        n2 = network.nodes(data=True)[e[1]]
        n1_lat, n1_long = n1.get("Latitude"), n1.get("Longitude")
        n2_lat, n2_long = n2.get("Latitude"), n2.get("Longitude")
        distance = geodesic((n1_lat, n1_long),
                            (n2_lat, n2_long)).meters  # in meters
        delay = (distance / SPEED_OF_LIGHT * 1000) * \
            PROPAGATION_FACTOR  # in milliseconds
        newnetwork.add_edge(mapping[e[0]], mapping[e[1]], latency=float(delay))

    nx.write_gpickle(newnetwork, outputfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int,  nargs='?',
                        default=0)
    parser.add_argument('--k', type=int, nargs='?',
                        default=10)
    parser.add_argument('--inputfile', type=str, nargs='?',
                        const=1)
    parser.add_argument('--outputfile', type=str, nargs='?',
                        const=1, default=r'./data/network.gpickle')
    args = parser.parse_args()
    cpu = (1, 500)
    memory = (1, 64)
    bandwidth = (1, 1000)

    if args.inputfile.endswith(".graphml"):
        graphml_reader(args.seed, cpu, memory, bandwidth, args.inputfile, args.outputfile)
    if args.inputfile.endswith(".gml"):
        gml_reader(args.seed, cpu, memory, bandwidth, args.inputfile, args.outputfile)
    else:
        generate_fatTree_graph(args.k, args.outputfile)
