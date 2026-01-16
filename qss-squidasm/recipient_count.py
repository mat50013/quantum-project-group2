import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import matplotlib.pyplot as plt
from simulate import simulate, get_qbers

def simulate_recipient_count_qber(recipient_count: int):
    print(f"Simulating for {recipient_count} recipients")
    start_time = time.time()

    dealer_results, recipients_results = simulate(
        "alice",
        [f"r{i}" for i in range(recipient_count)],
        32,
        128,
        0.99
    )

    qbers = get_qbers(dealer_results, recipients_results)

    print(f"Done for {recipient_count} recipients in {time.time() - start_time}s")

    return recipient_count, qbers

def plot_recipient_counts():
    start_time = time.time()

    recipient_counts = [2, 3, 4, 5, 10]
    qbers_per_count = {}

    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(simulate_recipient_count_qber, recipient_count)
            for recipient_count in recipient_counts
        ]

        for future in as_completed(futures):
            recipient_count, qbers = future.result()
            qbers_per_count[recipient_count] = qbers

    qbers_per_count = [qbers_per_count[recipient_count] for recipient_count in recipient_counts]

    recipient_count_labels = [str(recipient_count) for recipient_count in recipient_counts]

    plt.boxplot(
        qbers_per_count,
        tick_labels=recipient_count_labels,
        showmeans=True
    )

    plt.xlabel("Recipient count")
    plt.ylabel("QBER")
    plt.ylim(0, 1)
    plt.title("QBER vs Recipient count")

    plt.show()

    print()
    print(f"Simulation time: {time.time() - start_time}s")
    print("Mean QBER:")
    for recipient_count, qbers in zip(recipient_counts, qbers_per_count):
        print(f"\t{recipient_count} recipients: {np.mean(qbers)}")
