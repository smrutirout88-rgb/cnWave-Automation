import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from libraries.cnwave.workflow import OneTouchWorkflow
from libraries.cnwave.client import CnWaveClient
from libraries.cnwave.logger import setup_logger


class CnWaveControllerLib:

    def __init__(self):
        self.client = None
        self.workflow = None
        self.logger = setup_logger()

    # --------------------------------
    # CONNECT TO CONTROLLER
    # --------------------------------
    def connect_to_controller(self, host, username, password, port=3443):

        self.logger.info(f"Connecting to controller {host}...")

        self.client = CnWaveClient(
            host=host,
            username=username,
            password=password,
            port=port
        )

        self.workflow = OneTouchWorkflow(self.client)

        self.logger.info(f"Connected to controller {host}")

        return f"Connected to {host}"

    # --------------------------------
    # CREATE LINK WORKFLOW
    # --------------------------------
    def create_link_workflow(self, node_a_info, node_b_info):

        if not self.workflow:
            raise Exception("Controller not connected. Call 'Connect To Controller' first.")

        if not isinstance(node_a_info, dict) or not isinstance(node_b_info, dict):
            raise ValueError("Node info must be dictionaries")

        self.logger.info("Starting Create Link Workflow from Robot")

        result = self.workflow.create_link_workflow(
            node_a_info,
            node_b_info
        )

        self.logger.info("Create Link Workflow completed")

        return result

    # --------------------------------
    # GET TOPOLOGY
    # --------------------------------
    def get_topology(self):

        if not self.client:
            raise Exception("Controller not connected")

        return self.client.get_topology()

    # --------------------------------
    # GET LINKS
    # --------------------------------
    def get_links(self):

        if not self.client:
            raise Exception("Controller not connected")

        return self.client.get_links()

    def is_link_alive(self, node_a, node_b):
        if not self.client:
            raise Exception("Controller not connected")
        return self.client.is_link_alive(node_a, node_b)

    # --------------------------------
    # GET/SET NETWORK OVERRIDES
    # --------------------------------
    def get_network_overrides(self):
        if not self.client:
            raise Exception("Controller not connected")
        return self.client.get_network_overrides()

    def set_network_overrides(self, overrides):
        if not self.client:
            raise Exception("Controller not connected")
        return self.client.set_network_overrides(overrides)
    
    # --------------------------------
    # UPDATE TDD SLOT RATIO 
    # --------------------------------
    def update_tdd_slot_ratio(self, value):
        if not self.client:
            raise Exception("Controller not connected")
        return self.client.update_tdd_slot_ratio(value)
    
    # --------------------------------
    def get_current_tdd(self):
        if not self.client:
            raise Exception("Controller not connected")

        overrides = self.client.get_network_overrides_parsed()

        return overrides["radioParamsBase"]["fwParams"]["tddSlotRatio"]

    def set_tdd(self, value):
        if not self.client:
            raise Exception("Controller not connected")

        return self.client.update_tdd_slot_ratio(value)
    
    def get_current_mcs(self):
        if not self.client:
            raise Exception("Controller not connected")

        overrides = self.client.get_node_overrides_parsed()

        return overrides["PoP"]["linkParamsBase"]["fwParams"]["laMaxMcs"]
    
    def set_mcs(self, value):
        if not self.client:
            raise Exception("Controller not connected")

        return self.client.update_mcs(value)
    
    def wait_for_link_active(self, timeout=90):
        if not self.client:
            raise Exception("Controller not connected")

        return self.client.wait_for_link_active(timeout)






