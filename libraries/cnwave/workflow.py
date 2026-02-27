import time


class OneTouchWorkflow:

    def __init__(self, client):
        self.client = client
        self.logger = client.logger

    # -------------------------------------------------
    # HELPER: Generate names
    # -------------------------------------------------

    def generate_site_name(self, mac, model):
        mac_suffix = mac.replace(":", "")[-6:]
        return f"site-{model}-{mac_suffix}"

    def generate_node_name(self, mac, model):
        mac_suffix = mac.replace(":", "")[-6:]
        return f"node-{model}-{mac_suffix}"

    # -------------------------------------------------
    # STEP 1: CLEAR EXISTING TOPOLOGY
    # -------------------------------------------------

    def clear_topology(self):

        self.logger.info("Clearing existing topology...")
        topology = self.client.get_topology()

        # Delete links first
        for link in topology.get("links", []):
            payload = {
                "aNodeName": link.get("a_node_name"),
                "zNodeName": link.get("z_node_name"),
                "force": True
            }
            self.client.delete_link(payload)

        # Delete nodes
        for node in topology.get("nodes", []):
            payload = {
                "nodeName": node.get("name"),
                "force": True
            }
            self.client.delete_node(payload)

        # Delete sites
        for site in topology.get("sites", []):
            payload = {
                "siteName": site.get("name")
            }
            self.client.delete_site(payload)

        self.logger.info("Topology cleared")

    # -------------------------------------------------
    # STEP 2: ADD SITE
    # -------------------------------------------------

    def add_site(self, site_name, latitude, longitude):

        payload = {
            "site": {
                "name": site_name,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": 0,
                    "accuracy": 10000
                }
            }
        }

        self.logger.info(f"Adding site {site_name}")
        self.client.add_site(payload)

    # -------------------------------------------------
    # STEP 3: ADD NODE
    # -------------------------------------------------

    def add_node(self, node_name, mac, wlan_mac, model,
                 site_name, node_type, is_pop):

        payload = {
            "node": {
                "name": node_name,
                "node_type": node_type,
                "mac_addr": mac,
                "wlan_mac_addrs": [wlan_mac],
                "pop_node": is_pop,
                "site_name": site_name,
                "hw_model": model
            }
        }

        self.logger.info(f"Adding node {node_name}")
        self.client.add_node(payload)

    # -------------------------------------------------
    # STEP 4: ADD LINK
    # -------------------------------------------------

    def add_link(self, node_a, node_b, wlan_a, wlan_b):

        link_name = f"link-{node_a}-{node_b}"

        payload = {
            "link": {
                "name": link_name,
                "a_node_name": node_a,
                "z_node_name": node_b,
                "a_node_mac": wlan_a,
                "z_node_mac": wlan_b,
                "link_type": 1
            }
        }

        self.logger.info(f"Adding link {link_name}")
        self.client.add_link(payload)

        return link_name

    # -------------------------------------------------
    # STEP 5: WAIT FOR NODE ONLINE
    # -------------------------------------------------

    def wait_for_node(self, node_name, timeout=300):
        self.logger.info(f"Waiting for {node_name} to come online")
        self.client.wait_for_node_online(node_name, timeout)
        self.logger.info(f"{node_name} is online")

    # -------------------------------------------------
    # STEP 6: VALIDATE LINK
    # -------------------------------------------------

    def validate_link(self, node_a, node_b, timeout=120, interval=5):

        self.logger.info("Validating link status...")

        start = time.time()

        while time.time() - start < timeout:

            if self.client.is_link_alive(node_a, node_b):
                self.logger.info("Link is alive")
                return True

            time.sleep(interval)

        self.logger.error("Link failed to come alive")
        return False

    # -------------------------------------------------
    # MASTER WORKFLOW
    # -------------------------------------------------

    def create_link_workflow(self, node_a_info, node_b_info):

        self.logger.info("Starting One Touch Link Workflow")

        # 1. Clear topology
        self.clear_topology()

        # 2. Generate names
        site_a = self.generate_site_name(
            node_a_info["mac"],
            node_a_info["model"]
        )

        site_b = self.generate_site_name(
            node_b_info["mac"],
            node_b_info["model"]
        )

        node_a = self.generate_node_name(
            node_a_info["mac"],
            node_a_info["model"]
        )

        node_b = self.generate_node_name(
            node_b_info["mac"],
            node_b_info["model"]
        )

        # 3. Add sites
        self.add_site(site_a,
                      node_a_info["latitude"],
                      node_a_info["longitude"])

        self.add_site(site_b,
                      node_b_info["latitude"],
                      node_b_info["longitude"])

        # 4. Add nodes
        self.add_node(node_a,
                      node_a_info["mac"],
                      node_a_info["wlan_mac"],
                      node_a_info["model"],
                      site_a,
                      node_a_info["node_type"],
                      node_a_info["is_pop"])

        self.add_node(node_b,
                      node_b_info["mac"],
                      node_b_info["wlan_mac"],
                      node_b_info["model"],
                      site_b,
                      node_b_info["node_type"],
                      node_b_info["is_pop"])

        # 5. Add link
        link_name = self.add_link(
            node_a,
            node_b,
            node_a_info["wlan_mac"],
            node_b_info["wlan_mac"]
        )

        # 6. Wait for CN online
        self.wait_for_node(node_b)

        # 7. Validate link
        if not self.validate_link(node_a, node_b):
            return {
                "status": "FAILED",
                "reason": "Link did not come alive",
                "node_a": node_a,
                "node_b": node_b
            }

        self.logger.info("One Touch Link Workflow Completed Successfully")

        return {
            "status": "SUCCESS",
            "node_a": node_a,
            "node_b": node_b,
            "link_name": link_name
        }
