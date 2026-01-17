import time
from simulate import run_simulation
from concurrent.futures import ProcessPoolExecutor, as_completed
import matplotlib.pyplot as plt
import numpy as np

def basic():
    start_time = time.time()

    stats = run_simulation(
        "Alice",
        ["Bob", "Charlie"],
        n_rounds=100,
        eve_target=None,
        verbose=False
    )

    print(f"Simulation time: {time.time() - start_time:.2f}s")
    print(f"QBER: {stats['qber']:.2f}%")
    print(f"Secret sharing rate: {stats['ss_rate']:.1f}%")


def compare_eve():
    start_time = time.time()

    # Without Eve
    stats_clean = run_simulation("Alice", ["Bob", "Charlie"], 100)

    # With Eve intercepting Bob
    stats_eve = run_simulation("Alice", ["Bob", "Charlie"], 100, eve_target="Bob")

    print(f"Simulation time: {time.time() - start_time:.2f}s")
    print()
    print("Without Eve:")
    print(f"\tQBER: {stats_clean['qber']:.2f}%")
    print(f"\tSecret sharing: {stats_clean['ss_rate']:.1f}%")
    print()
    print("With Eve:")
    print(f"\tQBER: {stats_eve['qber']:.2f}%")
    print(f"\tSecret sharing: {stats_eve['ss_rate']:.1f}%")


def vary_recipients():
    start_time = time.time()

    recipient_lists = [
        ["Bob"],
        ["Bob", "Charlie"],
        ["Bob", "Charlie", "Diana"],
        ["Bob", "Charlie", "Diana", "Frank"],
    ]

    print("QBER by recipient count:")
    for recipients in recipient_lists:
        stats = run_simulation("Alice", recipients, 100)
        print(f"\t{len(recipients)+1} parties: {stats['qber']:.2f}%")

    print(f"\nSimulation time: {time.time() - start_time:.2f}s")

def simulate_fidelity_qber(fidelity: float):
    print(f"Simulating for {fidelity * 100:.1f}% link fidelity")
    start_time = time.time()

    qbers = []
    for _ in range(32):
        stats = run_simulation(
            "Alice",
            ["Bob", "Charlie", "Diana"],
            n_rounds=128,
            eve_target=None,
            fidelity=fidelity
        )
        qbers.append(stats['qber'] / 100)  # Convert to 0-1 range

    print(f"Done for {fidelity * 100:.1f}% in {time.time() - start_time:.1f}s")
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

    qbers_per_fidelity = [qbers_per_fidelity[f] for f in fidelities]
    fidelity_labels = [f"{f*100:.1f}%" for f in fidelities]

    plt.boxplot(qbers_per_fidelity, tick_labels=fidelity_labels, showmeans=True)
    plt.xlabel("Link fidelity")
    plt.ylabel("QBER")
    plt.ylim(0, 1)
    plt.title("QBER vs Link fidelity")
    plt.show()

    print(f"\nSimulation time: {time.time() - start_time:.1f}s")
    print("Mean QBER:")
    for fidelity, qbers in zip(fidelities, qbers_per_fidelity):
        print(f"\tFidelity {fidelity*100:.1f}%: {np.mean(qbers):.4f}")


def plot_eve_impact_fidelity(fidelities=None, recipients=None, n_trials=16):
    """
    Plot Eve's impact on QBER across different link fidelities.

    Args:
        fidelities: List of fidelity values (default: [0.75, 0.90, 0.95, 0.99, 0.999])
        recipients: List of recipient names or number of recipients (default: ["Bob", "Charlie"])
        n_trials: Number of trials per fidelity (default: 16)
    """
    if fidelities is None:
        fidelities = [0.75, 0.90, 0.95, 0.99, 0.999]

    if recipients is None:
        recipients = ["Bob", "Charlie"]
    elif isinstance(recipients, int):
        # Generate recipient names if given a number
        if not (2 <= recipients <= 7):
            raise ValueError("Number of recipients must be between 2 and 7")
        recipients = [chr(66 + i) for i in range(recipients)]  # B, C, D, E, F, G, H

    start_time = time.time()
    results = {}

    for fidelity in fidelities:
        qbers_clean = []
        qbers_eve = []

        for _ in range(n_trials):
            stats_clean = run_simulation("Alice", ["Bob", "Charlie"], 128, fidelity=fidelity)
            stats_eve = run_simulation("Alice", ["Bob", "Charlie"], 128, fidelity=fidelity, eve_target="Bob")
            qbers_clean.append(stats_clean['qber'] / 100)
            qbers_eve.append(stats_eve['qber'] / 100)

        results[fidelity] = {'clean': qbers_clean, 'eve': qbers_eve}

    # Prepare data for boxplot
    qbers_clean_list = [results[f]['clean'] for f in fidelities]
    qbers_eve_list = [results[f]['eve'] for f in fidelities]

    # Create side-by-side boxplots
    positions_clean = [i*2.5 for i in range(len(fidelities))]
    positions_eve = [i*2.5 + 0.8 for i in range(len(fidelities))]

    plt.figure(figsize=(12, 6))
    bp1 = plt.boxplot(qbers_clean_list, positions=positions_clean, widths=0.6,
                      patch_artist=True, showmeans=True, label="No Eve")
    bp2 = plt.boxplot(qbers_eve_list, positions=positions_eve, widths=0.6,
                      patch_artist=True, showmeans=True, label="Eve")

    # Color the boxes
    for patch in bp1['boxes']:
        patch.set_facecolor('lightblue')
    for patch in bp2['boxes']:
        patch.set_facecolor('lightcoral')

    # Set labels and limits
    fidelity_labels = [f"{f*100:.1f}%" for f in fidelities]
    plt.xticks([i*2.5 + 0.4 for i in range(len(fidelities))], fidelity_labels)
    plt.xlabel("Link Fidelity")
    plt.ylabel("QBER")
    plt.ylim(-0.05, 1)
    plt.title("Eve's Impact on QBER vs Link Fidelity")
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

    print(f"\nSimulation time: {time.time() - start_time:.1f}s")
    print(f"Recipients: {', '.join(recipients)}")
    print("\nMean QBER by fidelity:")
    print(f"{'Fidelity':<12} {'No Eve':<12} {'With Eve':<12} {'Difference':<12}")
    print("-" * 50)
    for fidelity in fidelities:
        clean_mean = np.mean(results[fidelity]['clean'])
        eve_mean = np.mean(results[fidelity]['eve'])
        diff = eve_mean - clean_mean
        print(f"{fidelity*100:>6.1f}%     {clean_mean:>10.4f}   {eve_mean:>10.4f}   {diff:>10.4f}")


if __name__ == "__main__":
    #basic()
    #compare_eve()
    # vary_recipients()
    #plot_fidelities()
    plot_eve_impact_fidelity(recipients=7)