#!/usr/bin/env python3

import requests
import networkx as nx
# import matplotlib.pyplot as plt
# modified matplotlib import to not cause crash in ubuntu 22.04 gnome GTK4 environment
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt

class FloodlightVisualizer:
    """
    Fetches topology from Floodlight and visualizes it with NetworkX.
    """

    def __init__(
        self,
        device_url="http://localhost:8080/wm/device/",
        links_url="http://localhost:8080/wm/topology/links/json"
    ):
        self.device_url = device_url
        self.links_url  = links_url

        self.topology   = nx.Graph()

    def fetch_json(self, url):
        """
        Safely fetch JSON from a given URL, handling errors.
        Returns Python data (list or dict), or None if something failed.
        """
        try:
            resp = requests.get(url, timeout=5)
        except requests.exceptions.RequestException as e:
            print(f"[Error] Failed to connect to {url}: {e}")
            return None

        if resp.status_code != 200:
            print(f"[Error] {url} returned status {resp.status_code}")
            print("Response text:", resp.text)
            return None

        # Attempt JSON decode
        try:
            return resp.json()
        except ValueError as e:
            print("[Error] Could not parse JSON:", e)
            print("Response text:", resp.text)
            return None

    def add_switch_links(self):
        """
        Reads /wm/topology/links/json and adds switch-to-switch edges.
        Switch node labeled as: s{dpid}
        """
        data = self.fetch_json(self.links_url)
        if not data or not isinstance(data, list):
            print("[Warning] /wm/topology/links/json did not return a list. No switch links added.")
            return

        for link in data:
            # link should have 'src-switch', 'dst-switch', 'src-port', 'dst-port'
            src_dpid = link.get("src-switch", "")
            dst_dpid = link.get("dst-switch", "")

            if not src_dpid or not dst_dpid:
                # Skip invalid entries
                continue

            src_label = f"s{src_dpid}"
            dst_label = f"s{dst_dpid}"

            # Add nodes to the graph (NetworkX will ignore duplicates)
            self.topology.add_node(src_label, type="switch")
            self.topology.add_node(dst_label, type="switch")

            # Add an edge for the link
            self.topology.add_edge(
                src_label,
                dst_label,
                src_port=link.get("src-port"),
                dst_port=link.get("dst-port"),
                link_type=link.get("type"),
                direction=link.get("direction")
            )

    def add_hosts(self):
        """
        Reads /wm/device/ data, and for each discovered host with a valid
        attachmentPoint, adds an edge host->switch.

        - Host labeled as "h{ip}"
        - Switch labeled as "s{dpid}"
        """
        data = self.fetch_json(self.device_url)
        if not data:
            print("[Warning] /wm/device/ returned no data. No hosts added.")
            return

        # Some Floodlight versions respond with a list of devices directly
        # Others respond with { "devices": [ ... ] }
        if isinstance(data, dict) and "devices" in data:
            devices = data["devices"]
        elif isinstance(data, list):
            devices = data
        else:
            # Unknown shape
            print("[Warning] /wm/device/ had an unexpected JSON shape. No hosts added.")
            return

        for dev in devices:
            # dev might be something like:
            # {
            #   "mac": "00:00:00:00:00:01",
            #   "ipv4": [ "10.0.0.1" ],
            #   "ipv6": [],
            #   "vlan": [ "none" ],
            #   "attachmentPoint": [
            #       {
            #         "switch": "00:00:00:00:00:00:00:01" OR "switchDPID": "00:...",
            #         "port": 1
            #       }
            #   ],
            #   ...
            # }
            if not isinstance(dev, dict):
                continue

            # MAC is optional in some builds, but let's see if it’s present
            mac = dev.get("mac", "")
            # IPv4 might be a list
            ipv4_list = dev.get("ipv4", [])

            # Must have an attachmentPoint
            ap_list = dev.get("attachmentPoint", [])
            if not ap_list or not isinstance(ap_list, list):
                continue

            # We'll take just the first AP
            ap = ap_list[0]
            # Some versions call it "switch", others "switchDPID"
            switch_dpid = ap.get("switch") or ap.get("switchDPID")
            port = ap.get("port")

            if not switch_dpid or port is None:
                # Invalid / incomplete
                continue

            # If we have no IPv4 address, skip, or we can fallback to MAC-based labeling
            if len(ipv4_list) == 0:
                # fallback to host label by mac
                host_label = f"h{mac}" if mac else None
            else:
                host_label = f"h{ipv4_list[0]}"

            if not host_label:
                continue

            # Add the host as a node
            self.topology.add_node(host_label, type="host")

            # The switch label must match what we used in add_switch_links
            switch_label = f"s{switch_dpid}"
            # If the switch node doesn't exist yet, add it (just to ensure it’s in the graph)
            self.topology.add_node(switch_label, type="switch")

            # Add edge host->switch
            self.topology.add_edge(
                host_label,
                switch_label,
                port=port
            )

    def build_topology(self):
        """
        Main function to build the topology from Floodlight data.
        """
        self.add_switch_links()
        self.add_hosts()

    def draw_topology(self):
        """
        Draw the built topology with matplotlib.
        Switches are squares, hosts are circles.
        """
        plt.figure(figsize=(8,6))

        # Simple layout
        pos = nx.spring_layout(self.topology, k=0.5, seed=42)

        # Separate switch nodes and host nodes
        switch_nodes = [n for n,d in self.topology.nodes(data=True) if d.get("type") == "switch"]
        host_nodes   = [n for n,d in self.topology.nodes(data=True) if d.get("type") == "host"]

        # Draw switches
        nx.draw_networkx_nodes(
            self.topology,
            pos,
            nodelist=switch_nodes,
            node_color="skyblue",
            node_shape="s",
            node_size=600,
            label="Switches"
        )

        # Draw hosts
        nx.draw_networkx_nodes(
            self.topology,
            pos,
            nodelist=host_nodes,
            node_color="lightgreen",
            node_shape="o",
            node_size=400,
            label="Hosts"
        )

        # Draw edges
        nx.draw_networkx_edges(self.topology, pos, width=1.5, edge_color="gray")

        # Label them
        nx.draw_networkx_labels(self.topology, pos, font_size=8, font_color="black")

        plt.title("Floodlight Network Topology")
        plt.axis("off")
        plt.legend()
        plt.show()

    def find_shortest_path(self, src_label, dst_label):
        """
        Attempt a shortest path in the built graph from src_label to dst_label.
        Returns the path as a list of nodes, or None if not found.
        """
        if src_label not in self.topology:
            print(f"[Error] Source node {src_label} not in graph.")
            return None
        if dst_label not in self.topology:
            print(f"[Error] Destination node {dst_label} not in graph.")
            return None

        try:
            path = nx.shortest_path(self.topology, source=src_label, target=dst_label)
            return path
        except nx.NetworkXNoPath:
            print(f"[Error] No path between {src_label} and {dst_label}")
            return None


if __name__ == "__main__":
    fv = FloodlightVisualizer()
    fv.build_topology()

    # Example: find shortest path between two host IP nodes
    path = fv.find_shortest_path("h10.0.0.1", "h10.0.0.3")
    if path:
        print("Shortest path from h10.0.0.1 to h10.0.0.3:", path)

    # Visualize it
    fv.draw_topology()
