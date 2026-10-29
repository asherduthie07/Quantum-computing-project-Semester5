"""Even–Mansour and Simon simulation primitives."""
from math import prod, pi
import random
import numpy as np
from scipy.stats import chisquare
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

# Qiskit count keys represent the measured x register as displayed bitstrings.
# Interpret each key with int(bitstring, 2) for GF(2) dot products.

def build_instance(P: list[int], k1: int, k2: int, n: int) -> dict:
    """Construct the cipher table and report the Simon promise checks."""
    size = 1 << n
    bijective = len(P) == size and sorted(P) == list(range(size))
    if len(P) != size or any(not isinstance(v, int) or v < 0 or v >= size for v in P) or not 0 <= k1 < size or not 0 <= k2 < size:
        return dict(P=list(P), E=[], f=[], x_xor_k1=[], collision_pairs=[], bijective=False, periodic=False, two_to_one=False, distinct_outputs=0, promise_ok=False, reasons=['Invalid table or keys'])
    E = [P[x ^ k1] ^ k2 for x in range(size)]
    f = [E[x] ^ P[x] for x in range(size)]
    periodic = k1 != 0 and all(f[x] == f[x ^ k1] for x in range(size))
    distinct = len(set(f))
    two_to_one = all(f.count(v) == 2 for v in set(f))
    flags = {'bijective': bijective, 'periodic': periodic, 'two_to_one': two_to_one}
    reasons = [f'{key} check failed' for key, value in flags.items() if not value]
    return dict(P=list(P), E=E, f=f, x_xor_k1=[x ^ k1 for x in range(size)], collision_pairs=[(x, x ^ k1) for x in range(size) if x < (x ^ k1) and f[x] == f[x ^ k1]], **flags, distinct_outputs=distinct, promise_ok=all(flags.values()) and distinct == size // 2, reasons=reasons)

def make_lookup_gate(table: list[int], name: str, n: int):
    """Construct the original reversible lookup gate."""
    gate = QuantumCircuit(2*n, name=name)
    input_bits = list(range(n))
    for x, value in enumerate(table):
        zero_controls = [i for i in range(n) if ((x >> i) & 1) == 0]
        for i in zero_controls: gate.x(i)
        for j in range(n):
            if (value >> j) & 1: gate.mcx(input_bits, n+j)
        for i in zero_controls: gate.x(i)
    return gate.to_gate(label=name)

def _gates(P: list[int], k1: int, k2: int, n: int):
    pg = make_lookup_gate(P, 'U_P', n)
    enc = QuantumCircuit(2*n, name='Encryption')
    for i in range(n):
        if (k1 >> i) & 1: enc.x(i)
    enc.append(pg, list(range(2*n)))
    for i in range(n):
        if (k1 >> i) & 1: enc.x(i)
    for i in range(n):
        if (k2 >> i) & 1: enc.x(n+i)
    return pg, enc.to_gate(label='U_E')

def build_circuit(P: list[int], k1: int, k2: int, n: int) -> QuantumCircuit:
    """Build the original measured Simon circuit."""
    pg, eg = _gates(P, k1, k2, n)
    x = QuantumRegister(n, 'x'); y = QuantumRegister(n, 'y'); c = ClassicalRegister(n, 'meas')
    qc = QuantumCircuit(x, y, c)
    qc.h(x); qc.barrier(); qc.append(eg, list(x)+list(y)); qc.append(pg, list(x)+list(y)); qc.barrier(); qc.h(x); qc.barrier(); qc.measure(x, c)
    return qc

def circuit_stats(qc: QuantumCircuit) -> dict:
    """Return depth, qubits and decomposed gate inventory."""
    decomposed = qc.decompose(reps=2)
    return {'depth': qc.depth(), 'gate_counts': dict(decomposed.count_ops()), 'qubits': qc.num_qubits}

def run_simon(qc: QuantumCircuit, shots: int = 4096, seed: int = 42) -> dict[str, int]:
    """Sample measured x-register counts."""
    return StatevectorSampler(seed=seed).run([qc], shots=shots).result()[0].data.meas.get_counts()

def stage_states(P: list[int], k1: int, k2: int, n: int) -> dict:
    """Return nonzero amplitudes at the four circuit stages and oracle groups."""
    pg, eg = _gates(P, k1, k2, n)
    qc = QuantumCircuit(2*n); stages = []
    def capture(name):
        amplitudes = []
        for index, a in enumerate(Statevector.from_instruction(qc).data):
            if abs(a) > 1e-12:
                amplitudes.append(dict(x=index % (1<<n), z=index >> n, re=float(a.real), im=float(a.imag), mag=float(abs(a)), phase=float(np.angle(a))))
        stages.append({'name': name, 'amplitudes': amplitudes})
    capture('after_init'); qc.h(range(n)); capture('after_H'); qc.append(eg, range(2*n)); qc.append(pg, range(2*n)); capture('after_oracle'); qc.h(range(n)); capture('after_final_H')
    groups = {}
    for a in stages[2]['amplitudes']: groups.setdefault(a['z'], []).append(a['x'])
    # Contributions of one input pair to each final x outcome (output fixed).
    coefficient = 1 / (1 << n)
    interference = []
    for y in range(1 << n):
        terms = [coefficient, coefficient * (-1 if (k1 & y).bit_count() % 2 else 1)]
        interference.append(dict(y=format(y, f'0{n}b'), terms=terms, sum=sum(terms), allowed=(k1 & y).bit_count() % 2 == 0))
    return {'stages': stages, 'oracle_groups': groups, 'interference': interference, 'pair_coefficient': coefficient}

def theory_distribution(k1: int, n: int) -> dict[str, float]:
    """Ideal distribution for a nonzero XOR period."""
    allowed = [i for i in range(1<<n) if (i & k1).bit_count() % 2 == 0]
    return {format(i, f'0{n}b'): (1/len(allowed) if i in allowed else 0.0) for i in range(1<<n)}

def tvd(counts: dict, theory: dict) -> float:
    """Total variation distance over all outcomes."""
    total = sum(counts.values())
    return .5 * sum(abs(counts.get(k, 0)/total - theory.get(k, 0)) for k in set(counts)|set(theory)) if total else 0.0

def chi_square(counts: dict, theory: dict) -> tuple[float, float]:
    """Pearson test on allowed support only; forbidden counts are excluded."""
    support = [k for k, p in theory.items() if p > 0]
    total = sum(counts.get(k, 0) for k in support)
    if not total or len(support) < 2: return (0.0, 1.0)
    result = chisquare([counts.get(k, 0) for k in support], [total*theory[k]/sum(theory[s] for s in support) for k in support])
    return float(result.statistic), float(result.pvalue)

def _rank(rows: list[int], n: int) -> int:
    rows = list(rows); rank = 0
    for bit in range(n-1, -1, -1):
        pivot = next((j for j in range(rank, len(rows)) if rows[j] >> bit & 1), None)
        if pivot is None: continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for j in range(len(rows)):
            if j != rank and rows[j] >> bit & 1: rows[j] ^= rows[rank]
        rank += 1
    return rank

def solve_gf2(counts_or_sample_sequence: dict | list[str], n: int, P: list[int] | None = None, k1: int | None = None, k2: int | None = None, order: str = 'sorted') -> dict:
    """Process measurements and recover the nonzero nullspace candidate, if unique."""
    if order not in ('sorted', 'sequence'): raise ValueError('order must be sorted or sequence')
    samples = list(counts_or_sample_sequence)
    if order == 'sorted': samples = sorted(set(samples))
    rows = []; considered = []
    for b in samples:
        y = int(b, 2); independent = _rank(rows+[y], n) > len(rows)
        if independent: rows.append(y)
        considered.append({'y': b, 'independent': independent, 'rank_after': len(rows)})
        if order == 'sorted' and len(rows) == n-1: break
    matrix = rows.copy(); steps = [{'op': 'initial', 'matrix': [format(v, f'0{n}b') for v in matrix]}]; rank = 0
    for bit in range(n-1, -1, -1):
        pivot = next((j for j in range(rank, len(matrix)) if matrix[j] >> bit & 1), None)
        if pivot is None: continue
        if pivot != rank:
            matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
            steps.append({'op': f'swap R{rank+1} R{pivot+1}', 'matrix': [format(v, f'0{n}b') for v in matrix]})
        for j in range(len(matrix)):
            if j != rank and matrix[j] >> bit & 1:
                matrix[j] ^= matrix[rank]; steps.append({'op': f'R{j+1} ← R{j+1} ⊕ R{rank+1}', 'matrix': [format(v, f'0{n}b') for v in matrix]})
        rank += 1
    nullspace = [s for s in range(1<<n) if all((y&s).bit_count()%2 == 0 for y in rows)]
    candidates = [s for s in nullspace if s]; recovered = candidates[0] if len(candidates)==1 else None
    rk2 = None; verification = []
    if recovered is not None and P is not None and k1 is not None and k2 is not None:
        instance = build_instance(P, k1, k2, n); rk2 = instance['E'][0] ^ P[recovered]
        verification = [dict(x=x, original=e, recovered=P[x ^ recovered]^rk2, match=e == (P[x ^ recovered]^rk2)) for x,e in enumerate(instance['E'])]
    return dict(measurements=considered, independent_rows=[format(y, f'0{n}b') for y in rows], steps=steps, nullspace=nullspace, candidates=candidates, recovered_k1=recovered, reason=None if recovered is not None else 'Measurements do not identify a unique nonzero period', recovered_k2=rk2, verification=verification, all_match=bool(verification) and all(r['match'] for r in verification))

def success_probability(t: int, n: int = 3) -> float:
    """Probability t uniform samples span an (n-1)-dimensional space: product (1-2**(i-t)), i=0..n-2."""
    return prod(1-2**(i-t) for i in range(n-1)) if t >= n-1 else 0.0

def monte_carlo_success(n: int, k1: int, t: int, trials: int, seed: int) -> float:
    """Estimate full-rank probability using independent ideal measurements."""
    rng = random.Random(seed); support = [int(b,2) for b,p in theory_distribution(k1,n).items() if p]
    return sum(_rank(rng.choices(support, k=t), n) == n-1 for _ in range(trials))/trials

def complexity_curves(n_max: int) -> dict:
    """Query growth; Simon is O(n), with order n-1 independent equations needed."""
    ns = list(range(1,n_max+1))
    return {'n': ns, 'brute_force': [2**n for n in ns], 'birthday': [2**(n/2) for n in ns], 'grover': [pi/4*2**(n/2) for n in ns], 'simon': ns}

def find_valid_permutation(k1: int, n: int, seed: int | None = None, max_tries: int = 100000) -> list[int] | None:
    """Search random permutations for the exact Simon promise."""
    rng = random.Random(seed); p = list(range(1<<n))
    for _ in range(max_tries):
        rng.shuffle(p)
        if build_instance(p,k1,0,n)['promise_ok']: return p.copy()
    return None

def failure_cases() -> list[dict]:
    """Return illustrative promise failures and their sampled solver outcomes."""
    cases = [('2-bit affine', [0,1,2,3], 1, 0, 2), ('identity', list(range(8)), 5, 3, 3), ('extra collisions', [0,1,2,3,4,5,7,6], 5, 0, 3)]
    result = []
    for name,p,k1,k2,n in cases:
        instance = build_instance(p,k1,k2,n); counts = run_simon(build_circuit(p,k1,k2,n), 256, 42); solved = solve_gf2(counts,n,order='sequence')
        result.append(dict(name=name,n=n,k1=k1,k2=k2,instance=instance,rank_reached=len(solved['independent_rows']),candidate_set_size=len(solved['candidates'])))
    return result
