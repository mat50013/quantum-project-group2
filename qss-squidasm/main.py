import time
import numpy as np
from simulate import simulate, get_qbers
from fidelity import plot_fidelities

def basic():
    start_time = time.time()

    dealer_results, recipients_results = simulate(
        "alice",
        ["bob", "charlie", "diana"],
        16,
        20,
        0.99
    )

    qbers = get_qbers(dealer_results, recipients_results)

    for i, qber in enumerate(qbers):
        print(f"Round {i}: {qber}")

    print()
    print(f"Simulation time: {time.time() - start_time}s")
    print(f"Mean QBER: {np.mean(qbers)}")

if __name__ == "__main__":
    # basic()
    plot_fidelities()