"""Standalone demonstration of the Even–Mansour Simon attack."""
from pathlib import Path
import matplotlib.pyplot as plt
from simon_core import build_instance, build_circuit, run_simon, theory_distribution, solve_gf2

N = 3
SHOTS = 4096
P = [0, 2, 3, 5, 4, 1, 6, 7]
SECRET_K1 = 0b101
SECRET_K2 = 0b011

def main():
    instance = build_instance(P, SECRET_K1, SECRET_K2, N)
    print('\n=== 1. EVEN-MANSOUR TRUTH TABLE ===')
    print(' x    P(x)  E(x)  f(x)')
    for x in range(1 << N):
        print(f"{x:03b}   {P[x]:03b}   {instance['E'][x]:03b}   {instance['f'][x]:03b}")
    print('\nPeriod and two-to-one promise:', 'VERIFIED' if instance['promise_ok'] else 'FAILED')
    qc = build_circuit(P, SECRET_K1, SECRET_K2, N)
    print('\n=== 2. QUANTUM CIRCUIT ===')
    print(qc.draw(output='text'))
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    qc.draw(output='mpl', fold=-1).savefig(output_dir / 'simon_circuit.png', dpi=200, bbox_inches='tight')
    counts = run_simon(qc, SHOTS, 42)
    print('\n=== 3. QUANTUM SIMULATION ===\nSimulator: Qiskit StatevectorSampler')
    print(f'Qubits: {2*N}\nShots: {SHOTS}')
    for b in sorted(counts): print(f'Measured {b}: {counts[b]}')
    theory = theory_distribution(SECRET_K1, N)
    print('\n=== 4. THEORY VS SIMULATION ===\nOutcome  Theory    Simulation')
    for b, prob in theory.items(): print(f'{b}      {prob:.4f}    {counts.get(b,0)/SHOTS:.4f}')
    fig, ax = plt.subplots(figsize=(10, 5))
    positions = list(range(1 << N))
    ax.bar([i-.19 for i in positions], list(theory.values()), width=.38, label='Theoretical')
    ax.bar([i+.19 for i in positions], [counts.get(b, 0)/SHOTS for b in theory], width=.38, label='Qiskit simulation')
    ax.set_xticks(positions, list(theory)); ax.set_xlabel('Measured bitstring'); ax.set_ylabel('Probability')
    ax.set_title("Simon's Algorithm: Theory vs Qiskit Simulation"); ax.legend(); ax.grid(axis='y', alpha=.25)
    fig.tight_layout(); fig.savefig(output_dir / 'theory_vs_simulation.png', dpi=200)
    assert all(theory[b] for b in counts)
    print('\nTheoretical support matches simulation: PASS')
    solved = solve_gf2(counts, N, P, SECRET_K1, SECRET_K2)
    print('\n=== 5. MEASURED EQUATIONS ===')
    for y in solved['independent_rows']: print(f'y = {y}: y dot k1 = 0 (mod 2)')
    print('\n=== 6. FINAL RESULTS ===')
    print(f"Recovered k1 = {solved['recovered_k1']:03b}")
    print(f"Recovered k2 = {solved['recovered_k2']:03b}")
    print(f"All 8 encryption outputs verified: {solved['all_match']}")
    assert solved['all_match'] and solved['recovered_k1'] == SECRET_K1 and solved['recovered_k2'] == SECRET_K2
    print("\nSUCCESS: Simon's algorithm recovered both keys.")
    print("Graphs saved in the outputs/ folder.")
    plt.show()

if __name__ == '__main__': main()
