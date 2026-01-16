from typing import List

import numpy as np
from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from squidasm.run.stack.config import HeraldedLinkConfig

from squidasm.run.stack.run import run
from squidasm.util.util import create_complete_graph_network
from programs.dealer_program import DealerProgram
from programs.recipient_program import RecipientProgram

def simulate(dealer_name: str, recipient_names: List[str], num_states: int, num_times: int, fidelity: float):
    node_names = [dealer_name] + recipient_names

    link_length = 5

    cfg = create_complete_graph_network(
        node_names,
        "heralded",
        HeraldedLinkConfig(length=link_length, emission_fidelity=fidelity),
        clink_typ="default",
        clink_cfg=DefaultCLinkConfig(length=link_length),
    )

    programs = {dealer_name: DealerProgram(dealer_name, recipient_names, num_states)} | {
        recipient_name: RecipientProgram(recipient_name, dealer_name, recipient_names, num_states) for
        recipient_name in recipient_names}

    results = run(config=cfg, programs=programs, num_times=num_times)

    dealer_results = []
    recipients_results = [[] for _ in range(num_times)]

    for n in range(num_times):
        dealer_result = results[0][n]['result']
        dealer_results.append(dealer_result)

        for i in range(len(recipient_names)):
            recipient_result = results[i + 1][n]['result']
            recipients_results[n].append(recipient_result)

    return dealer_results, recipients_results

def get_qbers(dealer_results: List[np.ndarray], recipients_results: List[List[np.ndarray]]):
    qbers = []

    for dealer_result, recipients_result in zip(dealer_results, recipients_results):
        parity = np.zeros_like(dealer_result)

        for recipient_result in recipients_result:
            parity = np.bitwise_xor(parity, recipient_result)

        qber = np.not_equal(dealer_result, parity).sum() / parity.size
        qbers.append(qber)

    return qbers