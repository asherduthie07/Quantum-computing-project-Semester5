from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)
PARAMS = dict(n=3,P=[0,2,3,5,4,1,6,7],k1=5,k2=3)

def test_defaults_health():
    assert client.get('/api/health').json() == {'status':'ok'}
    assert client.get('/api/defaults').json() == {**PARAMS,'shots':4096,'seed':42}

def test_instance_validation_and_promise():
    assert client.post('/api/instance',json=PARAMS).json()['promise_ok']
    bad = client.post('/api/instance',json={**PARAMS,'P':[0]*8})
    assert bad.status_code == 422 and 'permutation' in bad.json()['detail']
    failed = client.post('/api/instance',json={**PARAMS,'P':list(range(8))})
    assert failed.status_code == 200 and not failed.json()['promise_ok']
    assert client.post('/api/run',json={**PARAMS,'shots':0}).status_code == 422
    assert client.get('/api/circuit.svg?P=broken').status_code == 422

def test_run_solve():
    body = {**PARAMS,'shots':4096,'seed':42}
    run = client.post('/api/run',json=body).json()
    assert run['counts'] == {'000':1050,'010':1024,'101':987,'111':1035}
    assert len(run['sequence']) == 4096 and run['support_ok']
    assert run['circuit_stats']['qubits'] == 6
    solve = client.post('/api/solve',json=body).json()
    assert solve['recovered_k1'] == 5 and solve['recovered_k2'] == 3 and solve['all_match']
    assert [m['y'] for m in solve['measurements']] == run['sequence']

def test_stages_and_svg():
    stages = client.post('/api/stages',json=PARAMS).json()
    assert len(stages['stages']) == 4
    for stage in stages['stages']:
        assert abs(sum(a['mag']**2 for a in stage['amplitudes'])-1) < 1e-10
    assert all(len(xs)==2 for xs in stages['oracle_groups'].values())
    svg = client.get('/api/circuit.svg')
    assert svg.status_code == 200 and '<svg' in svg.text
    assert svg.headers['content-type'].startswith('image/svg+xml')
    assert client.get('/api/circuit.svg').text == svg.text

def test_curves_failures_random():
    curve = client.post('/api/success-curve',json={'n':3,'k1':5,'t_max':4,'trials':100,'seed':42}).json()
    assert curve['theory'][1]['probability'] == .375
    assert len(curve['monte_carlo']) == 4
    complexity = client.get('/api/complexity?n_max=64').json()
    assert complexity['brute_force'][-1] == 2**64
    failures = client.get('/api/failure-cases').json()
    assert len(failures)==3
    assert [f['instance']['distinct_outputs'] for f in failures] == [1,1,2]
    assert [f['rank_reached'] for f in failures[:2]] == [0,0]
    assert [f['candidate_set_size'] for f in failures[:2]] == [3,7]
    random = client.post('/api/random-instance',json={'n':3,'seed':42}).json()
    assert client.post('/api/instance',json=random).json()['promise_ok']

def test_errors_and_cors():
    assert client.get('/api/missing').json()['error'] == 'request_error'
    response = client.options('/api/run',headers={'Origin':'http://localhost:5173','Access-Control-Request-Method':'POST'})
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'

def test_stage_interference_matches_final_support():
    data = client.post('/api/stages', json=PARAMS).json()
    assert data['pair_coefficient'] == 1/8
    rows = {r['y']: r for r in data['interference']}
    assert {y for y,r in rows.items() if r['allowed']} == {'000','010','101','111'}
    assert all(r['sum'] == (0.25 if r['allowed'] else 0) for r in rows.values())
    final_x = {format(a['x'], '03b') for a in data['stages'][-1]['amplitudes']}
    assert final_x == {y for y,r in rows.items() if r['allowed']}
