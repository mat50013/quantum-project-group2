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
            # Fixed: now uses the recipients parameter
            stats_clean = run_simulation("Alice", recipients, 128, fidelity=fidelity)
            stats_eve = run_simulation("Alice", recipients, 128, fidelity=fidelity, eve_target=recipients[0])
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
def simulate_recipient_count_qber(recipient_count: int):
    print(f"Simulating for {recipient_count} recipients")
    start_time = time.time()

    recipients = [f"r{i}" for i in range(recipient_count)]

    qbers = []
    for _ in range(32):
        stats = run_simulation(
            "alice",
            recipients,
            n_rounds=128,
            eve_target=None,
            fidelity=0.99
        )
        qbers.append(stats['qber'] / 100)  # Convert to 0-1 range

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
    plt.ylim(0, 0.35)
    plt.title("QBER vs Recipient count")

    plt.show()

    print()
    print(f"Simulation time: {time.time() - start_time}s")
    print("Mean QBER:")
    for recipient_count, qbers in zip(recipient_counts, qbers_per_count):
        print(f"\t{recipient_count} recipients: {np.mean(qbers)}")


def plot_detection_confidence(
        recipients=None,
        fidelities=None,
        round_counts=None,
        n_trials=30,
        confidence_target=0.99
):
    """
    Plot Eve detection confidence vs protocol rounds for different fidelities.

    Args:
        recipients: List of recipient names or int for count (default: 3)
        fidelities: List of fidelity values to compare (default: [0.95, 0.99, 0.999])
        round_counts: List of round counts to test (default: [10, 25, 50, 100, 200])
        n_trials: Number of trials per data point (default: 30)
        confidence_target: Target detection probability (default: 0.99)
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from simulate import run_simulation

    # Handle recipients
    if recipients is None:
        recipients = ["Bob", "Charlie", "Diana"]
    elif isinstance(recipients, int):
        if not (1 <= recipients <= 10):
            raise ValueError("Recipients must be between 1 and 10")
        recipients = [f"R{i+1}" for i in range(recipients)]

    # Defaults
    if fidelities is None:
        fidelities = [0.95, 0.99, 0.999]
    if round_counts is None:
        round_counts = [10, 25, 50, 100, 200]

    print(f"Configuration:")
    print(f"  Recipients: {len(recipients)} ({', '.join(recipients)})")
    print(f"  Fidelities: {fidelities}")
    print(f"  Round counts: {round_counts}")
    print(f"  Trials per point: {n_trials}")
    print()

    results = {}

    for fidelity in fidelities:
        print(f"\n{'='*50}")
        print(f"Testing fidelity: {fidelity*100:.1f}%")
        print('='*50)

        # Establish baseline threshold for this fidelity
        print("Establishing baseline (no Eve)...")
        baseline_qbers = []
        for i in range(n_trials):
            stats = run_simulation(
                "Alice", recipients, 200,
                fidelity=fidelity, verbose=False
            )
            if stats['valid_rounds'] > 0:
                baseline_qbers.append(stats['qber'])

        threshold = np.percentile(baseline_qbers, 95)
        baseline_mean = np.mean(baseline_qbers)
        baseline_std = np.std(baseline_qbers)
        print(f"  Baseline QBER: {baseline_mean:.2f}% ± {baseline_std:.2f}%")
        print(f"  Detection threshold (95th pct): {threshold:.2f}%")

        # Test each round count
        detection_probs = []
        false_positive_rates = []
        eve_qbers = []

        for n_rounds in round_counts:
            print(f"\n  Testing {n_rounds} rounds...")

            eve_detected = 0
            clean_false_alarms = 0
            round_eve_qbers = []

            for _ in range(n_trials):
                # With Eve
                stats_eve = run_simulation(
                    "Alice", recipients, n_rounds,
                    eve_target=recipients[0],
                    fidelity=fidelity, verbose=False
                )
                if stats_eve['valid_rounds'] > 0:
                    round_eve_qbers.append(stats_eve['qber'])
                    if stats_eve['qber'] > threshold:
                        eve_detected += 1

                # Without Eve
                stats_clean = run_simulation(
                    "Alice", recipients, n_rounds,
                    fidelity=fidelity, verbose=False
                )
                if stats_clean['valid_rounds'] > 0 and stats_clean['qber'] > threshold:
                    clean_false_alarms += 1

            detection_prob = eve_detected / n_trials
            false_positive = clean_false_alarms / n_trials

            detection_probs.append(detection_prob)
            false_positive_rates.append(false_positive)
            eve_qbers.append(np.mean(round_eve_qbers) if round_eve_qbers else 0)

            print(f"    Detection: {detection_prob*100:.1f}% | FP: {false_positive*100:.1f}% | Eve QBER: {eve_qbers[-1]:.1f}%")

        results[fidelity] = {
            'threshold': threshold,
            'baseline_mean': baseline_mean,
            'baseline_std': baseline_std,
            'detection_probs': detection_probs,
            'false_positive_rates': false_positive_rates,
            'eve_qbers': eve_qbers
        }

    # Plotting
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(fidelities)))

    # Plot 1: Detection probability vs rounds
    ax1 = axes[0]
    for idx, fidelity in enumerate(fidelities):
        ax1.plot(
            round_counts,
            results[fidelity]['detection_probs'],
            '-o', color=colors[idx], linewidth=2, markersize=8,
            label=f'Fidelity {fidelity*100:.1f}%'
        )

    ax1.axhline(y=confidence_target, color='red', linestyle='--',
                alpha=0.7, linewidth=2, label=f'{confidence_target*100:.0f}% Target')
    ax1.set_xlabel('Number of Protocol Rounds', fontsize=12)
    ax1.set_ylabel('Eve Detection Probability', fontsize=12)
    ax1.set_ylim(0, 1.05)
    ax1.set_title('Eve Detection Rate vs Protocol Rounds', fontsize=14)
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY: Rounds needed for target detection confidence")
    print("="*70)
    print(f"{'Fidelity':<12} {'Threshold':<12} {'QBER Gap':<12} {'Rounds for ' + str(int(confidence_target*100)) + '%':<15}")
    print("-"*70)

    best_fidelity = None
    best_rounds = float('inf')

    for fidelity in fidelities:
        r = results[fidelity]
        qber_gap = np.mean(r['eve_qbers']) - r['baseline_mean']

        rounds_needed = ">500"
        for i, prob in enumerate(r['detection_probs']):
            if prob >= confidence_target:
                rounds_needed = round_counts[i]
                if rounds_needed < best_rounds:
                    best_rounds = rounds_needed
                    best_fidelity = fidelity
                break

        print(f"{fidelity*100:>6.1f}%     {r['threshold']:>8.2f}%    {qber_gap:>8.2f}%     {rounds_needed}")

    print("-"*70)
    if best_fidelity:
        print(f"✓ BEST: {best_fidelity*100:.1f}% fidelity — achieves {confidence_target*100:.0f}% detection in {best_rounds} rounds")
    else:
        print(f"✗ No fidelity achieved {confidence_target*100:.0f}% detection within tested rounds")

    return results


if __name__ == "__main__":
    #basic()
    #compare_eve()
    # vary_recipients()
    #plot_fidelities()
    #plot_eve_impact_fidelity(recipients=7)
    #plot_recipient_counts()
    plot_detection_confidence(
        recipients=5,
        fidelities=[0.75, 0.81, 0.90, 0.95, 0.999],
        round_counts=[10, 25, 50, 100],
        n_trials=50,
        confidence_target=0.99
    )
