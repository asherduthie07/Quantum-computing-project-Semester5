"""Live, eight-step Even–Mansour demonstration using real Qiskit measurements."""
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
from simon_core import build_instance, build_circuit, run_simon, theory_distribution, tvd
from recovery_explanation import recover_from_measurements

N = 3
SHOTS = 1024
P = [0, 2, 3, 5, 4, 1, 6, 7]
SECRET_K1 = 0b101
SECRET_K2 = 0b011


def main(show=True, shots=SHOTS, seed=42):
    b = lambda value: format(value, f'0{N}b')
    def heading(step, title):
        print(f'\n{"=" * 72}\nSTEP {step} — {title}\n{"=" * 72}')
    instance = build_instance(P, SECRET_K1, SECRET_K2, N)
    heading(1, 'THE ORIGINAL ENCRYPTION PROBLEM')
    print('E(x) = P(x XOR k1) XOR k2\nf(x) = E(x) XOR P(x)')
    print('x: plaintext; P: public permutation; k1: first secret input mask; k2: second secret output mask.')
    print('Objective: recover k1 from quantum measurements, then calculate k2 from a known ciphertext.')
    print('Binary strings are written most significant bit first; counts and shots are decimal.')
    print(f'Teaching setup only (not recovery answers): k1 = {b(SECRET_K1)}, k2 = {b(SECRET_K2)}.')
    print('P = [' + ', '.join(map(b, P)) + ']')
    heading(2, 'HOW ENCRYPTION WORKS')
    print(' x  | P(x) | x XOR k1 | E(x) | f(x)')
    for x in range(1 << N):
        print(f'{b(x)} | {b(P[x])}  |    {b(x ^ SECRET_K1)}   | {b(instance["E"][x])}  | {b(instance["f"][x])}')
    x = 1
    shifted = x ^ SECRET_K1
    print(f'\nWorked example: x = {b(x)}')
    print(f'1. x XOR k1 = {b(x)} XOR {b(SECRET_K1)} = {b(shifted)}')
    print(f'2. P({b(shifted)}) = {b(P[shifted])} (public lookup)')
    print(f'3. E({b(x)}) = {b(P[shifted])} XOR {b(SECRET_K2)} = {b(instance["E"][x])}')
    print(f'4. f({b(x)}) = {b(instance["E"][x])} XOR P({b(x)})')
    print(f'5. f({b(x)}) = {b(instance["E"][x])} XOR {b(P[x])} = {b(instance["f"][x])}')
    heading(3, 'WHY THE FIRST KEY IS A HIDDEN PERIOD')
    print('f(x) = P(x XOR k1) XOR k2 XOR P(x)')
    print('f(x XOR k1) = P((x XOR k1) XOR k1) XOR k2 XOR P(x XOR k1)')
    print(f'Since k1 XOR k1 = {b(0)}, this becomes:')
    print('= P(x) XOR k2 XOR P(x XOR k1)\n= P(x XOR k1) XOR k2 XOR P(x)\n= f(x)')
    print('XOR can be reordered, so f(x XOR k1) = f(x): k1 is the hidden XOR period.')
    for a, partner in instance['collision_pairs']:
        print(f'f({b(a)}) = f({b(partner)}) = {b(instance["f"][a])}; {b(a)} XOR {b(partner)} = {b(a ^ partner)}')
    print(f'Exactly two inputs per output: {instance["two_to_one"]}; distinct outputs: {instance["distinct_outputs"]}')
    print(f'Simon exact two-to-one promise: {instance["promise_ok"]}')
    heading(4, 'THE ACTUAL QUANTUM CIRCUIT')
    print(f'1. Initialize {N} input and {N} output qubits to zero ({2*N} qubits).')
    print('2. First Hadamards create a superposition of every input.')
    print('3. Reversible U_E followed by U_P XORs f(x) into the output register.')
    print('4. Second input Hadamards cause interference: incompatible outcomes cancel.')
    print('5. Measure the input qubits.\n6. Collect equations y dot k1 = 0 (mod 2).')
    qc = build_circuit(P, SECRET_K1, SECRET_K2, N)
    print(qc.draw(output='text'))
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    circuit_fig = qc.draw(output='mpl', fold=-1)
    circuit_fig.savefig(output_dir / 'simon_circuit.png', dpi=200, bbox_inches='tight')
    heading(5, 'ACTUAL SIMULATOR MEASUREMENTS')
    counts = run_simon(qc, shots, seed)
    theory = theory_distribution(SECRET_K1, N)
    print(f'Qiskit StatevectorSampler · shots = {shots} · seed = {seed}')
    print('Theory uses the teaching setup for comparison only; recovery uses measured equations.')
    print('Outcome | Actual count | Actual probability | Theory')
    for outcome, probability in theory.items():
        count = counts.get(outcome, 0)
        print(f'{outcome}     | {count:12d} | {count}/{shots} = {count/shots:7.2%} | {probability:7.2%}')
    print('Use the observed strings as equations. 000 gives 0 = 0 and adds no information.')
    print('Finite-shot probabilities fluctuate; agreement does not mean identical percentages.')
    fig, ax = plt.subplots(figsize=(10, 5))
    positions = list(range(1 << N))
    ax.bar([i-.19 for i in positions], list(theory.values()), width=.38, label='Theoretical')
    ax.bar([i+.19 for i in positions], [counts.get(v, 0)/shots for v in theory], width=.38, label='Qiskit simulation')
    ax.set_xticks(positions, list(theory)); ax.set_xlabel('Measured bitstring (binary)'); ax.set_ylabel('Probability')
    ax.set_title("Simon's Algorithm: Theory vs Qiskit Simulation"); ax.legend(); ax.grid(axis='y', alpha=.25)
    fig.tight_layout(); fig.savefig(output_dir / 'theory_vs_simulation.png', dpi=200)
    heading(6, 'RECOVER THE FIRST KEY WITH SIMPLE EQUATIONS')
    solved = recover_from_measurements(counts, N, P, instance['E'])
    print('\n'.join(solved['explanation']))
    first, second = solved['recovered_k1'], solved['recovered_k2']
    heading(7, 'CALCULATE THE SECOND KEY')
    print('E(x) = P(x XOR k1) XOR k2')
    print('XOR both sides with P(x XOR k1); equal terms cancel:')
    print('k2 = E(x) XOR P(x XOR k1)')
    if first is not None:
        print(f'Choose x = {b(0)}. Use the observed ciphertext and the recovered first key:')
        print(f'1. E({b(0)}) = {b(instance["E"][0])} (original cipher table)')
        print(f'2. Recovered k1 = {b(first)}')
        print(f'3. {b(0)} XOR {b(first)} = {b(first)}')
        print(f'4. P({b(first)}) = {b(P[first])} (public lookup)')
        print(f'5. k2 = {b(instance["E"][0])} XOR {b(P[first])}')
        print(f'6. k2 = {b(second)}\nRecovered second key: k2 = {b(second)}')
    else:
        print('Cannot derive a unique second key without a unique first key. Try more shots.')
    heading(8, 'VERIFY BOTH RECOVERED KEYS')
    print('E_recovered(x) = P(x XOR recovered_k1) XOR recovered_k2')
    print(' x  | Original E(x) | Reconstructed E(x) | Match?')
    for row in solved['verification']:
        print(f'{b(row["x"])} |      {b(row["original"])}      |        {b(row["recovered"])}         | {"PASS" if row["match"] else "FAIL"}')
    support_ok = all(theory.get(value, 0) > 0 for value in counts)
    distance = tvd(counts, theory)
    # Explicit demonstration criterion, not a claim of identical probabilities.
    agreement = instance['promise_ok'] and support_ok and distance <= .10
    print(f'Recovered k1 = {b(first) if first is not None else "unresolved"}')
    print(f'Recovered k2 = {b(second) if second is not None else "unresolved"}')
    print(f'All {1 << N} encryption outputs verified = {solved["all_match"]}')
    print(f'Agreement criterion: promise holds, no forbidden outcomes, total variation distance <= 0.10. Actual distance = {distance:.6f}')
    print(f'Theoretical and simulated results agree = {agreement}')
    success = solved['all_match'] and agreement
    print('SUCCESS: both keys recovered and all checks passed.' if success else 'NOT VERIFIED: one or more checks failed or recovery is incomplete.')
    print('Saved outputs/simon_circuit.png and outputs/theory_vs_simulation.png')
    if show:
        plt.show()
    plt.close('all')
    return success


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-show', action='store_true', help='Save plots without opening windows')
    parser.add_argument('--shots', type=int, default=SHOTS)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.shots < 1 or not 0 <= args.seed < 2**32:
        parser.error('shots must be positive and seed must be between 0 and 4294967295')
    raise SystemExit(0 if main(not args.no_show, args.shots, args.seed) else 1)
