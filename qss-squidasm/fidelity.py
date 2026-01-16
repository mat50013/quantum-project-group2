import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import matplotlib.pyplot as plt
from simulate import simulate, get_qbers

def simulate_fidelity_qber(fidelity: float):
    print(f"Simulating for {fidelity * 100:.1f}% link fidelity")
    dealer_results, recipients_results = simulate(
        "alice",
        ["bob", "charlie", "diana"],
        32,
        50,
        fidelity
    )

    qbers = get_qbers(dealer_results, recipients_results)
    return fidelity, qbers

def plot_fidelities():
    start_time = time.time()

    fidelities = [0.75, 0.90, 0.95, 0.99, 0.999]
    qbers_per_fidelity = {}

    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(simulate_fidelity_qber, fidelity)
            for fidelity in fidelities
        ]

        for future in as_completed(futures):
            fidelity, qbers = future.result()
            qbers_per_fidelity[fidelity] = qbers

    qbers_per_fidelity = [qbers_per_fidelity[fidelity] for fidelity in fidelities]
    fidelity_labels = [f"{fidelity*100:.1f}%" for fidelity in fidelities]

    plt.boxplot(
        qbers_per_fidelity,
        tick_labels=fidelity_labels,
        showmeans=True
    )

    plt.xlabel("Link fidelity")
    plt.ylabel("QBER")
    plt.title("QBER vs Link fidelity")

    plt.show()

    print()
    print(f"Simulation time: {time.time() - start_time}s")
    print("Mean QBER:")
    for fidelity, qbers in zip(fidelities, qbers_per_fidelity):
        print(f"\tFidelity {fidelity*100:.1f}%: {np.mean(qbers)}")

# Non-parallel implementation kept for reference
def plot_fidelities_sequential():
    start_time = time.time()

    fidelities = [0.75, 0.90, 0.95, 0.99, 0.999]
    qbers_per_fidelity = []

    for fidelity in fidelities:
        _, qbers = simulate_fidelity_qber(fidelity)
        qbers_per_fidelity.append(qbers)

    fidelity_labels = [f"{fidelity*100:.1f}%" for fidelity in fidelities]

    plt.boxplot(
        qbers_per_fidelity,
        tick_labels=fidelity_labels,
        showmeans=True
    )

    plt.xlabel("Link fidelity")
    plt.ylabel("QBER")
    plt.title("QBER vs Link fidelity")

    plt.show()

    print()
    print(f"Simulation time: {time.time() - start_time}s")
    print("Mean QBER:")
    for fidelity, qbers in zip(fidelities, qbers_per_fidelity):
        print(f"\tFidelity {fidelity*100:.1f}%: {np.mean(qbers)}")