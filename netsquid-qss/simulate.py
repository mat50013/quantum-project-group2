import netsquid as ns
from typing import Dict, List
from network import create_network, reset_network
from ghz_resource import distribute_ghz_state, distribute_ghz_with_eve
from protocols import DealerProtocol, PartyProtocol
from eve import EveInterceptProtocol
from validation import is_valid_round, check_ghz_parity, verify_secret_sharing

def run_single_round(nodes: Dict, dealer_name: str, recipient_names: List[str], eve_node=None, eve_target: str = None) -> Dict:
    reset_network(nodes, eve_node)
    ns.sim_reset()

    if eve_node and eve_target:
        eve_protocol, _ = distribute_ghz_with_eve(nodes, dealer_name, recipient_names, eve_node, eve_target, EveInterceptProtocol)
    else:
        distribute_ghz_state(nodes, dealer_name, recipient_names)

    all_parties = [dealer_name] + recipient_names

    dealer_protocol = DealerProtocol(nodes[dealer_name], dealer_name, recipient_names)

    recipient_protocols = {}
    for recipient in recipient_names:
        other_parties = [p for p in all_parties if p != recipient]
        protocol = PartyProtocol(nodes[recipient], recipient, other_parties)
        recipient_protocols[recipient] = protocol

    dealer_protocol.start()
    for protocol in recipient_protocols.values():
        protocol.start()

    ns.sim_run(duration=1000)

    bases = {dealer_name: dealer_protocol.basis}
    outcomes = {dealer_name: dealer_protocol.outcome}

    for recipient, protocol in recipient_protocols.items():
        bases[recipient] = protocol.basis
        outcomes[recipient] = protocol.outcome

    valid = is_valid_round(bases)
    parity_passed = check_ghz_parity(bases, outcomes) if valid else None
    ss_success, ss_reconstructed, ss_actual = verify_secret_sharing(bases, outcomes, dealer_name) if valid else (None, None, None)

    return {
        "bases": bases,
        "outcomes": outcomes,
        "valid": valid,
        "parity_passed": parity_passed,
        "secret_sharing_success": ss_success,
        "reconstructed": ss_reconstructed,
        "actual": ss_actual,
    }


def run_simulation(dealer_name: str, recipient_names: List[str], n_rounds: int, eve_target: str = None, verbose: bool = False, fidelity: float = 1.0) -> Dict:
    nodes, eve_node = create_network(dealer_name, recipient_names, eve_target, fidelity)

    valid_rounds = 0
    passed_rounds = 0
    ss_successes = 0

    results_list = []
    for i in range(n_rounds):
        result = run_single_round(nodes, dealer_name, recipient_names, eve_node, eve_target)
        results_list.append(result)

        if result["valid"]:
            valid_rounds += 1
            if result["parity_passed"]:
                passed_rounds += 1
            if result["secret_sharing_success"]:
                ss_successes += 1

    error_rounds = valid_rounds - passed_rounds
    qber = (error_rounds / valid_rounds * 100) if valid_rounds > 0 else 0
    ss_rate = (ss_successes / valid_rounds * 100) if valid_rounds > 0 else 0
    return {
        "n_rounds": n_rounds,
        "valid_rounds": valid_rounds,
        "passed_rounds": passed_rounds,
        "error_rounds": error_rounds,
        "qber": qber,
        "ss_successes": ss_successes,
        "ss_rate": ss_rate,
        "eve_present": eve_target is not None,
        "eve_target": eve_target,
        "results": results_list,
    }