from itertools import combinations
from pathlib import Path
import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from simon_core import _gates, build_circuit, build_instance, run_simon
from recovery_explanation import recover_from_measurements

P = [0, 2, 3, 5, 4, 1, 6, 7]
E = [2, 7, 4, 5, 1, 3, 6, 0]


def test_reversible_oracles_on_every_input_and_output():
    pg, eg = _gates(P, 5, 3, 3)
    # Every input and output basis state checks reversibility, not just z=0.
    for x in range(8):
        for z in range(8):
            state = Statevector.from_int(x + (z << 3), 64)
            encrypted = state.evolve(eg)
            assert np.isclose(abs(encrypted.data[x + ((z ^ E[x]) << 3)]), 1)
            combined = encrypted.evolve(pg)
            assert np.isclose(abs(combined.data[x + ((z ^ E[x] ^ P[x]) << 3)]), 1)


def test_actual_1024_shot_recovery():
    counts = run_simon(build_circuit(P, 5, 3, 3), 1024, 42)
    assert sum(counts.values()) == 1024
    assert set(counts) <= {'000', '010', '101', '111'}
    result = recover_from_measurements(counts, 3, P, E)
    assert result['selected'] == ['010', '101']
    assert result['recovered_k1'] == 5
    assert result['recovered_k2'] == E[0] ^ P[5] == 3
    assert len(result['verification']) == 8 and result['all_match']


@pytest.mark.parametrize('pair', list(combinations(['010', '101', '111'], 2)))
def test_every_alternative_pair(pair):
    result = recover_from_measurements(list(reversed(pair)), 3, P, E)
    assert set(result['selected']) == set(pair)
    assert result['possible'] == [0, 5]
    assert result['all_match'] and result['recovered_k1'] == 5
    text = '\n'.join(result['explanation'])
    assert 'b = 0' in text
    assert 'a = c' in text
    assert '(0, 0, 0) = 000' in text and '(1, 0, 1) = 101' in text
    assert not any(word in text.lower() for word in ['matrix', 'gaussian', 'row reduction'])


def test_missing_measurements_do_not_fabricate_recovery():
    result = recover_from_measurements({'000': 10, '010': 0}, 3, P, E)
    assert result['selected'] == []
    assert result['recovered_k1'] is None and result['recovered_k2'] is None
    assert not result['all_match']
    contradictory = recover_from_measurements(['100', '010', '001'], 3, P, E)
    assert contradictory['candidates'] == []


def test_recovery_not_tied_to_teaching_keys():
    # All nonzero periods, using their ideal equation sets and independent cipher tables.
    for key in range(1, 8):
        observed = [format(y, '03b') for y in range(8) if (y & key).bit_count() % 2 == 0]
        cipher = build_instance(P, key, 6, 3)['E']
        result = recover_from_measurements(observed, 3, P, cipher)
        assert (result['recovered_k1'], result['recovered_k2']) == (key, 6)
        assert result['all_match']


def test_live_demo_output_and_artifacts(tmp_path, monkeypatch, capsys):
    import even_mansour_simon as demo
    monkeypatch.chdir(tmp_path)
    assert demo.main(show=False)
    output = capsys.readouterr().out
    for step in range(1, 9):
        assert f'STEP {step}' in output
    for text in ['b = 0', 'a = c', 'Recovered k1 = 101', 'Recovered k2 = 011',
                 'All 8 encryption outputs verified = True', 'SUCCESS']:
        assert text in output
    assert not any(word in output.lower() for word in ['matrix', 'gaussian', 'row reduction'])
    for name in ['simon_circuit.png', 'theory_vs_simulation.png']:
        assert (Path('outputs') / name).stat().st_size > 1000


def test_website_uses_shared_explanation():
    source = Path('web/src/sections/KeyRecovery.tsx').read_text()
    assert 'solved.explanation' in source
    assert 'solved.steps' not in source and 'matrix' not in source.lower()
