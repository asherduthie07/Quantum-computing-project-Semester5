from simon_core import *

P = [0,2,3,5,4,1,6,7]

def test_golden():
    inst = build_instance(P,5,3,3)
    assert inst['E'] == [2,7,4,5,1,3,6,0]
    assert inst['f'] == [2,5,7,0,5,2,0,7]
    assert inst['promise_ok']
    counts = run_simon(build_circuit(P,5,3,3),4096,42)
    assert counts == {'000':1050,'010':1024,'101':987,'111':1035}
    result = solve_gf2(counts,3,P,5,3)
    assert (result['recovered_k1'], result['recovered_k2'], result['all_match']) == (5,3,True)
    assert len(result['verification']) == 8

def test_support():
    qc = build_circuit(P,5,3,3)
    for seed in range(20):
        assert set(run_simon(qc,128,seed)) <= {'000','010','101','111'}

def test_probability():
    for t in range(2,17): assert abs(success_probability(t)-(1-2**-t)*(1-2**(1-t))) < 1e-12

def test_search():
    for seed in range(25):
        k = seed % 7 + 1
        p = find_valid_permutation(k,3,seed)
        assert p is not None and build_instance(p,k,0,3)['promise_ok']

def test_failures():
    assert all(not c['instance']['promise_ok'] for c in failure_cases())
