"""FastAPI interface for the Even–Mansour Simon simulator."""
from functools import lru_cache
from io import StringIO
from time import perf_counter
import random
from threading import Lock
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException
from qiskit.primitives import StatevectorSampler
from simon_core import (build_instance, build_circuit, circuit_stats, theory_distribution,
                        tvd, chi_square, solve_gf2, stage_states, success_probability,
                        monte_carlo_success, complexity_curves, find_valid_permutation,
                        failure_cases)
from server.schemas import Instance, Run, Success, RandomInstance

app = FastAPI(title='Simon simulator')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'], allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    detail = '; '.join(f"{'.'.join(map(str,e['loc']))}: {e['msg']}" for e in exc.errors())
    return JSONResponse(status_code=422, content={'error': 'validation_error', 'detail': detail})

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={'error': 'request_error', 'detail': str(exc.detail)})

@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={'error': 'simulation_error', 'detail': 'The simulation could not be completed. Check the parameters and retry.'})

def params(body):
    return dict(P=body.P, k1=body.k1, k2=body.k2, n=body.n)

@app.get('/api/health')
def health(): return {'status': 'ok'}

@app.get('/api/defaults')
def defaults(): return dict(n=3, P=[0,2,3,5,4,1,6,7], k1=5, k2=3, shots=4096, seed=42)

@app.post('/api/instance')
def instance(body: Instance): return build_instance(**params(body))

def sample(body):
    qc = build_circuit(**params(body))
    data = StatevectorSampler(seed=body.seed).run([qc], shots=body.shots).result()[0].data.meas
    return qc, data.get_counts(), data.get_bitstrings()[:8192]

@app.post('/api/run')
def run(body: Run):
    started = perf_counter()
    qc, counts, sequence = sample(body)
    theory = theory_distribution(body.k1, body.n)
    stat, p_value = chi_square(counts, theory)
    return dict(counts=counts, theory=theory, tvd=tvd(counts,theory), chi2={'stat':stat, 'p_value':p_value}, support_ok=all(theory.get(b,0)>0 for b in counts), circuit_stats=circuit_stats(qc), sequence=sequence, runtime_ms=(perf_counter()-started)*1000)

@app.post('/api/solve')
def solve(body: Run):
    _, _, sequence = sample(body)
    return solve_gf2(sequence, body.n, body.P, body.k1, body.k2, order='sequence')

@app.post('/api/stages')
def stages(body: Instance): return stage_states(**params(body))

_draw_lock = Lock()
@lru_cache(maxsize=32)
def draw(n, P, k1, k2):
    with _draw_lock, plt.rc_context({'text.color':'#E8ECF8', 'axes.edgecolor':'#E8ECF8'}):
        qc = build_circuit(list(P), k1, k2, n)
        fig = qc.draw(output='mpl', fold=-1, style={'backgroundcolor':'none', 'textcolor':'#E8ECF8', 'linecolor':'#E8ECF8', 'creglinecolor':'#97A0BC', 'gatetextcolor':'#E8ECF8', 'gatefacecolor':'#22304B', 'barrierfacecolor':'#22304B'})
        try:
            out = StringIO(); fig.savefig(out, format='svg', transparent=True, bbox_inches='tight')
            return out.getvalue()
        finally: plt.close(fig)

@app.get('/api/circuit.svg')
def circuit(n: int = Query(3, ge=1, le=6), P: str = '0,2,3,5,4,1,6,7', k1: int = 5, k2: int = 3):
    try: body = Instance(n=n, P=[int(v) for v in P.split(',')], k1=k1, k2=k2)
    except ValueError as exc: return JSONResponse(status_code=422, content={'error':'validation_error', 'detail':str(exc)})
    return Response(draw(body.n, tuple(body.P), body.k1, body.k2), media_type='image/svg+xml')

@app.post('/api/success-curve')
def success(body: Success):
    return {'theory':[{'t':t, 'probability':success_probability(t,body.n)} for t in range(1,body.t_max+1)], 'monte_carlo':[{'t':t, 'probability':monte_carlo_success(body.n,body.k1,t,body.trials,body.seed+t)} for t in range(1,body.t_max+1)]}

@app.get('/api/complexity')
def complexity(n_max: int = Query(64, ge=1, le=64)): return complexity_curves(n_max)

@app.get('/api/failure-cases')
def failures(): return failure_cases()

@app.post('/api/random-instance')
def random_instance(body: RandomInstance):
    rng = random.Random(body.seed); k1 = body.k1 or rng.randrange(1,1<<body.n)
    P = find_valid_permutation(k1,body.n,body.seed,max_tries=1000)
    if P is None: return JSONResponse(status_code=503, content={'error':'search_exhausted', 'detail':'No valid permutation found; retry with another seed.'})
    return dict(n=body.n,P=P,k1=k1,k2=rng.randrange(1<<body.n))
