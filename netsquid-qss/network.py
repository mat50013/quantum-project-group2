from netsquid.nodes import Node
from netsquid.components import QuantumMemory, QuantumChannel, ClassicalChannel
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components.models.delaymodels import FixedDelayModel

def create_noisy_channel(name: str, length: float, fidelity: float):
    delay_model = FixedDelayModel(delay=length * 5)
    if fidelity >= 1.0:
        return QuantumChannel(name, length=length, models={"delay_model": delay_model})
    depolar_rate = 4 * (1 - fidelity) / 3
    noise_model = DepolarNoiseModel(depolar_rate=depolar_rate, time_independent=True)
    return QuantumChannel(name, length=length, models={"quantum_noise_model": noise_model, "delay_model": delay_model})

def create_network(dealer_name: str, recipient_names: list, eve_target: str = None, fidelity: float = 1.0):
    nodes = {}

    dealer = Node(dealer_name)
    dealer_mem = QuantumMemory(f"{dealer_name}Memory", num_positions=len(recipient_names) + 1)
    dealer.add_subcomponent(dealer_mem, name="memory")
    nodes[dealer_name] = dealer

    for name in recipient_names:
        node = Node(name)
        mem = QuantumMemory(f"{name}Memory", num_positions=1)
        node.add_subcomponent(mem, name="memory")
        nodes[name] = node

    eve_node = None
    if eve_target and eve_target in recipient_names:
        eve_node = Node("Eve")
        eve_mem = QuantumMemory("EveMemory", num_positions=1)
        eve_node.add_subcomponent(eve_mem, name="memory")

    _setup_ports(nodes, dealer_name, recipient_names, eve_node, eve_target)
    _setup_channels(nodes, dealer_name, recipient_names, eve_node, eve_target, fidelity)
    return nodes, eve_node


def _setup_ports(nodes, dealer_name, recipient_names, eve_node, eve_target):
    dealer = nodes[dealer_name]

    dealer_ports = []
    for recipient in recipient_names:
        dealer_ports.extend([
            f"q_port_to{recipient}",
            f"c_port_to{recipient}",
            f"c_port_from{recipient}"
        ])
    if eve_node:
        dealer_ports.append("q_port_toEve")
    dealer.add_ports(dealer_ports)

    for recipient in recipient_names:
        node = nodes[recipient]
        ports = [
            f"q_port_from{dealer_name}",
            f"c_port_from{dealer_name}",
            f"c_port_to{dealer_name}"
        ]
        for other in recipient_names:
            if other != recipient:
                ports.extend([f"c_port_to{other}", f"c_port_from{other}"])
        if eve_target == recipient:
            ports.append("q_port_fromEve")
        node.add_ports(ports)

    if eve_node:
        eve_node.add_ports([
            f"q_port_from{dealer_name}",
            f"q_port_to{eve_target}"
        ])

def _setup_channels(nodes, dealer_name, recipient_names, eve_node, eve_target, fidelity):
    dealer = nodes[dealer_name]

    for recipient in recipient_names:
        recipient_node = nodes[recipient]

        if eve_target == recipient and eve_node:
            qc_to_eve = create_noisy_channel(f"QC_{dealer_name}_Eve", 5, fidelity)
            qc_to_eve.ports["send"].connect(dealer.ports["q_port_toEve"])
            qc_to_eve.ports["recv"].connect(eve_node.ports[f"q_port_from{dealer_name}"])

            qc_from_eve = QuantumChannel(f"QC_Eve_{recipient}", length=5)
            qc_from_eve.ports["send"].connect(eve_node.ports[f"q_port_to{eve_target}"])
            qc_from_eve.ports["recv"].connect(recipient_node.ports["q_port_fromEve"])
        else:
            qc = create_noisy_channel(f"QC_{dealer_name}_{recipient}", 10, fidelity)
            qc.ports["send"].connect(dealer.ports[f"q_port_to{recipient}"])
            qc.ports["recv"].connect(recipient_node.ports[f"q_port_from{dealer_name}"])

        cc_to = ClassicalChannel(f"CC_{dealer_name}_to_{recipient}", length=10)
        cc_to.ports["send"].connect(dealer.ports[f"c_port_to{recipient}"])
        cc_to.ports["recv"].connect(recipient_node.ports[f"c_port_from{dealer_name}"])

        cc_from = ClassicalChannel(f"CC_{recipient}_to_{dealer_name}", length=10)
        cc_from.ports["send"].connect(recipient_node.ports[f"c_port_to{dealer_name}"])
        cc_from.ports["recv"].connect(dealer.ports[f"c_port_from{recipient}"])

    for i, r1 in enumerate(recipient_names):
        for r2 in recipient_names[i+1:]:
            node1, node2 = nodes[r1], nodes[r2]

            cc_1to2 = ClassicalChannel(f"CC_{r1}_to_{r2}", length=10)
            cc_1to2.ports["send"].connect(node1.ports[f"c_port_to{r2}"])
            cc_1to2.ports["recv"].connect(node2.ports[f"c_port_from{r1}"])

            cc_2to1 = ClassicalChannel(f"CC_{r2}_to_{r1}", length=10)
            cc_2to1.ports["send"].connect(node2.ports[f"c_port_to{r1}"])
            cc_2to1.ports["recv"].connect(node1.ports[f"c_port_from{r2}"])

def reset_network(nodes, eve_node=None):
    for node in nodes.values():
        node.subcomponents["memory"].reset()
    if eve_node:
        eve_node.subcomponents["memory"].reset()