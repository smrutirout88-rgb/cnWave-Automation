import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from libraries.cnwave.exceptions import (
    AuthenticationError,
    ApiRequestError,
    ApiTimeoutError,
    ApiConnectionError,
)

from libraries.cnwave.retry import retry
from libraries.cnwave.logger import setup_logger



class CnWaveClient:

    def __init__(self, host, username, password,
                 port=3443, verify_ssl=False, timeout=15):

        self.base_url = f"https://{host}:{port}"
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        self.session = requests.Session()
        self.session.verify = False
        self.token = None

        self.logger = setup_logger()

        self.authenticate()

    # -----------------------------------------
    # Authentication
    # -----------------------------------------

    def authenticate(self):
        self.logger.info("Authenticating with CNWave controller")

        url = f"{self.base_url}/local/userLogin"

        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise AuthenticationError("Login failed")

            self.token = data.get("message")

            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

            self.logger.info("Authentication successful")

        except requests.exceptions.Timeout:
            raise ApiTimeoutError("Authentication timeout")

        except requests.exceptions.ConnectionError:
            raise ApiConnectionError("Unable to connect to controller")

        except Exception as e:
            raise AuthenticationError(str(e))

    # -----------------------------------------
    # Generic Request Handler
    # -----------------------------------------

    @retry(max_attempts=5)
    def request(self, method, endpoint, payload=None):

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
            method,
            url,
            json=payload,
            verify=self.verify_ssl,
            timeout=self.timeout
        )

            # Handle token expiry
            if response.status_code == 401:
                self.logger.warning("Token expired. Re-authenticating...")
                self.authenticate()
                response = self.session.request(
                    method,
                    url,
                    json=payload,
                    verify=self.verify_ssl,
                    timeout=self.timeout
                )

            response.raise_for_status()

            if not response.text.strip():
                self.logger.warning(f"Empty response from {endpoint}")
                return {}

            try:
                data = response.json()
            except Exception:
                self.logger.error(f"Non-JSON response from {endpoint}")
                self.logger.error(response.text)
                raise ApiRequestError("Controller returned non-JSON response")

            if isinstance(data, dict) and not data.get("success", True):
                raise ApiRequestError(data)

            return data

        except requests.exceptions.Timeout:
            raise ApiTimeoutError("API request timeout")

        except requests.exceptions.ConnectionError:
            raise ApiConnectionError("API connection error")

        except Exception as e:
            raise ApiRequestError(str(e))

    # -----------------------------------------
    # Inventory / Topology Read APIs
    # -----------------------------------------

    def get_topology(self):
        response = self.request(
            "POST",
            "/api/getTopology",
            payload={}
        )
        return response.get("message", response)

    def get_nodes(self):
        response = self.request(
            "GET",
            "/api/getNodes"
        )
        return response.get("nodes", [])

    def get_links(self):
        topo = self.get_topology()
        return topo.get("links", [])

    def get_node(self, name):
        for node in self.get_nodes():
            if node.get("name") == name:
                return node
        return None
    
    def get_node_info(self):

        response = self.request(
            "POST",
            "/api/getNodeInfo",
            payload={}
        )

        self.logger.warning(f"NODE INFO RESPONSE: {response}")
        return response

    def get_system_capability(self):

        response = self.request(
            "POST",
            "/local/getSystemCapability",
            payload={}
        )

        self.logger.warning(f"SYSTEM CAPABILITY RESPONSE: {response}")

        return response

    def is_link_alive(self, node_a, node_b):
        for link in self.get_links():
            if (
                link.get("a_node_name") == node_a and
                link.get("z_node_name") == node_b
            ):
                return link.get("is_alive", False)
        return False

    def wait_for_node_online(self, node_name, timeout=300, interval=10):

        start = time.time()

        while time.time() - start < timeout:
            node = self.get_node(node_name)

            if node and node.get("status") == 3:
                return True

            time.sleep(interval)

        raise ApiTimeoutError(f"Node {node_name} did not come online")

    # -----------------------------------------
    # Topology Management APIs
    # -----------------------------------------

    def add_site(self, payload):
        return self.request(
            "POST",
            "/internal/api/addSite",
            payload=payload
        )

    def add_node(self, payload):
        return self.request(
            "POST",
            "/internal/api/addNode",
            payload=payload
        )

    def add_link(self, payload):
        return self.request(
            "POST",
            "/internal/api/addLink",
            payload=payload
        )

    def delete_link(self, payload):
        return self.request(
            "POST",
            "/internal/api/delLink",
            payload=payload
        )

    def delete_node(self, payload):
        return self.request(
            "POST",
            "/internal/api/delNode",
            payload=payload
        )

    def delete_site(self, payload):
        return self.request(
            "POST",
            "/internal/api/delSite",
            payload=payload
        )

    # -----------------------------------------
    # Link Control APIs
    # -----------------------------------------

    def set_ignition_state(self, payload):
        return self.request(
            "POST",
            "/internal/api/setIgnitionState",
            payload=payload
        )

    def set_link_status(self, payload):
        return self.request(
            "POST",
            "/internal/api/setLinkStatus",
            payload=payload
        )

    # -----------------------------------------
    # Override APIs
    # -----------------------------------------

    def set_node_overrides(self, payload):
        return self.request(
            "POST",
            "/internal/api/setNodeOverridesConfig",
            payload=payload
        )

    # -----------------------------------------
    # Controller Config APIs
    # -----------------------------------------

    def get_controller_config(self):
        return self.request(
            "POST",
            "/internal/api/getControllerConfig",
            payload={}
        )

    def set_controller_config(self, payload):
        return self.request(
            "POST",
            "/internal/api/setControllerConfig",
            payload=payload
        )

    # -----------------------------------------
    # Network Overrides (Onboard API)
    # -----------------------------------------

    def get_node_overrides_parsed(self):
        import json

        response = self.request(
            "POST",
            "/api/getNodeOverridesConfig",
            payload={}
        )

        overrides_str = response.get("overrides")

        if not overrides_str:
            return {}

        return json.loads(overrides_str)

    def update_mcs(self, value):
        import json
        import time

        response = self.request(
            "POST",
            "/api/getNodeOverridesConfig",
            payload={}
        )

        overrides_str = response.get("overrides")

        if not overrides_str:
            raise Exception("Node overrides empty")

        overrides = json.loads(overrides_str)

        # Apply to ALL nodes present in overrides
        for node_name in overrides.keys():

            if "linkParamsBase" not in overrides[node_name]:
                overrides[node_name]["linkParamsBase"] = {}

            if "fwParams" not in overrides[node_name]["linkParamsBase"]:
                overrides[node_name]["linkParamsBase"]["fwParams"] = {}

            overrides[node_name]["linkParamsBase"]["fwParams"]["laMaxMcs"] = int(value)

        payload = {
            "overrides": json.dumps(overrides)
        }

        result = self.request(
            "POST",
            "/api/setNodeOverridesConfig",
            payload=payload
        )

        time.sleep(4)
        return result

    def get_network_overrides(self):
        response = self.request(
            "POST",
            "/api/getNetworkOverridesConfig",
            payload={}
        )

        # Controller usually returns:
        # { "overrides": "{...json string...}" }

        overrides = response.get("overrides")

        if isinstance(overrides, str):
            import json
            return json.loads(overrides)

        return overrides

    def get_network_overrides_parsed(self):
        return self.get_network_overrides()

    def set_network_overrides(self, overrides_dict):
        import json

        # Controller expects overrides as stringified JSON
        overrides_str = json.dumps(overrides_dict)

        payload = {
            "overrides": overrides_str
        }

        return self.request(
            "POST",
            "/api/setNetworkOverridesConfig",
            payload=payload
        )

    def update_tdd_slot_ratio(self, value):
        import json

        # 1️⃣ Get full existing overrides
        response = self.request(
            "POST",
            "/api/getNetworkOverridesConfig",
            payload={}
        )

        overrides_str = response.get("overrides")

        if not overrides_str:
            raise Exception("Network overrides are empty. Cannot modify safely.")

        overrides = json.loads(overrides_str)

        # 2️⃣ Modify ONLY if structure already exists
        if "radioParamsBase" in overrides:
            if "fwParams" in overrides["radioParamsBase"]:
                overrides["radioParamsBase"]["fwParams"]["tddSlotRatio"] = int(value)
            else:
                raise Exception("fwParams missing inside radioParamsBase")
        else:
            raise Exception("radioParamsBase missing in network overrides")

        # 3️⃣ Send FULL modified blob back
        payload = {
            "overrides": json.dumps(overrides)
        }

        return self.request(
            "POST",
            "/api/setNetworkOverridesConfig",
            payload=payload
        )
    # -----------------------------------------
    # Runtime / Wait Helpers
    # -----------------------------------------

    def wait_for_link_active(self, timeout=90, interval=5):
        timeout = float(timeout)
        interval = float(interval)

        start = time.time()

        while time.time() - start < timeout:
            links = self.get_links()

            for link in links:
                if link.get("is_alive"):
                    return True

            time.sleep(interval)

        return False

    def get_dn_radio_mac(self):
        nodes = self.request("GET", "/api/getNodes")
        for node in nodes.get("nodes", []):
            if node.get("nodeType") == "DN":
                return node.get("macAddr")
        return None
    
    def wait_for_link_stable(self, timeout=300, interval=5, stable_window=60):
        import time

        timeout = float(timeout)
        interval = float(interval)
        stable_window = float(stable_window)

        start_time = time.time()

        # Step 1: Wait until link first comes up
        while time.time() - start_time < timeout:
            if any(link.get("is_alive") for link in self.get_links()):
                break
            time.sleep(interval)
        else:
            return False

        # Step 2: Ensure it stays up continuously
        stable_start = time.time()

        while time.time() - start_time < timeout:
            if not any(link.get("is_alive") for link in self.get_links()):
                # Link flapped → reset stability timer
                stable_start = None
                while not any(link.get("is_alive") for link in self.get_links()):
                    if time.time() - start_time >= timeout:
                        return False
                    time.sleep(interval)
                stable_start = time.time()
            else:
                if stable_start and (time.time() - stable_start >= stable_window):
                    return True

            time.sleep(interval)

        return False


    def get_pop_dn_versions(self, pop_name=None, dn_name=None):
        """
        Gets POP and DN software versions from /api/getCtrlStatusDump
        Matches nodes by pop_node flag from topology, then looks up
        cambiumVersion by MAC address in statusReports
        """
        try:
            # Get status dump - keyed by MAC address
            status_dump = self.request("POST", "/api/getCtrlStatusDump", payload={})
            status_reports = status_dump.get("statusReports", {})

            # Get topology to map node name → MAC → pop_node flag
            topo = self.get_topology()
            nodes = topo.get("nodes", [])

            pop_version = "unknown"
            dn_version  = "unknown"

            for node in nodes:
                name    = node.get("name", "")
                mac     = node.get("mac_addr", "")
                is_pop  = node.get("pop_node", False)

                # Look up this node's status report by MAC
                report  = status_reports.get(mac, {})
                version = report.get("cambiumVersion", "unknown")

                if is_pop:
                    # Match by name if provided, otherwise take first POP
                    if pop_name is None or pop_name == "None" or name == pop_name:
                        pop_version = version

                else:
                    # Match by name if provided, otherwise take first non-POP
                    if dn_name is None or dn_name == "None" or name == dn_name:
                        dn_version = version

            self.logger.info(f"POP version: {pop_version} | DN version: {dn_version}")
            return pop_version, dn_version

        except Exception as e:
            self.logger.warning(f"Could not get versions: {e}")
            return "unknown", "unknown"
        
    def get_software_version(self):
        """
        Returns software version from /local/getDeviceInfo
        Returns: dict with swVer, fwVersion, model, type
        """
        try:
            response = self.request("POST", "/local/getDeviceInfo", payload={})
            return {
                "swVer":      response.get("swVer", "unknown").strip(),
                "fwVersion":  response.get("fwVersion", "unknown").strip(),
                "model":      response.get("model", "unknown"),
                "type":       response.get("type", "unknown"),
            }
        except Exception as e:
            self.logger.warning(f"Could not get software version: {e}")
            return {
                "swVer": "unknown",
                "fwVersion": "unknown",
                "model": "unknown",
                "type": "unknown"
            }
        
    def debug_node_versions(self):
        """
        Debug helper - dumps topology nodes and node status
        Used by debug_find_version.robot
        """
        import json

        self.logger.warning("=== TOPOLOGY NODES ===")
        try:
            topo = self.get_topology()
            nodes = topo.get("nodes", [])
            if not nodes:
                self.logger.warning("No nodes found in topology")
            for node in nodes:
                self.logger.warning(json.dumps(node, indent=2))
        except Exception as e:
            self.logger.warning(f"getTopology failed: {e}")

        self.logger.warning("=== CTRL STATUS DUMP ===")
        try:
            status = self.request("POST", "/api/getCtrlStatusDump", payload={})
            # Only log cambiumVersion per node to keep output clean
            reports = status.get("statusReports", {})
            for mac, report in reports.items():
                self.logger.warning(
                    f"MAC: {mac} | "
                    f"cambiumVersion: {report.get('cambiumVersion')} | "
                    f"hardwareBoardId: {report.get('hardwareBoardId')}"
                )
        except Exception as e:
            self.logger.warning(f"getCtrlStatusDump failed: {e}")