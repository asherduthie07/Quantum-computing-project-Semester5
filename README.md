# Simon Observatory — Even–Mansour Quantum Attack

An educational demonstration of Simon’s algorithm applied to the Even–Mansour block cipher. The project combines a Qiskit simulator, a FastAPI backend, and an interactive React interface to explain how a hidden XOR period can reveal the cipher’s keys.

You can run the browser application or a standalone Python demonstration that prints the results and generates circuit and distribution plots. All quantum execution uses a local statevector simulator; no quantum hardware account or API key is required.

## Contents

- [Quick start](#quick-start)
- [Using the web application](#using-the-web-application)
- [Standalone Python demonstration](#standalone-python-demonstration)
- [How the algorithm works](#how-the-algorithm-works)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Testing and building](#testing-and-building)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)

## Quick start

### Prerequisites

- Python with support for the packages in `requirements.txt` (the source uses Python 3.10+ syntax).
- Node.js and npm compatible with Vite 6.
- A terminal and a modern browser.

The backend depends on FastAPI, Uvicorn, Pydantic, Qiskit **2.6.1**, NumPy, SciPy, Matplotlib, and pylatexenc. Pytest and HTTPX support the tests. Frontend versions are defined in `web/package.json` and locked in `web/package-lock.json`.

### 1. Install the Python dependencies

Open a terminal in the project root, the directory containing `simon_core.py`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If a working `.venv` already exists, skip its creation and activate it. On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.

### 2. Start the API

From the project root with the virtual environment activated:

```bash
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

Keep this terminal running. Useful endpoints:

- Health check: <http://localhost:8000/api/health>
- Interactive API documentation: <http://localhost:8000/docs>
- OpenAPI schema: <http://localhost:8000/openapi.json>

### 3. Start the frontend

Open a second terminal in the project root:

```bash
cd web
npm ci
npm run dev
```

Open **<http://localhost:5173>**. If Vite chooses another port, use the URL printed in its terminal.

The frontend sends requests to relative `/api` URLs. During development, `web/vite.config.ts` proxies those requests to `http://localhost:8000`. Both processes must remain running for simulations to work.

After installation, future sessions only require activating the environment, starting Uvicorn, and running `npm run dev` in `web`. Stop each process with **Ctrl+C**.

## Using the web application

The main page presents the problem, measured distribution, cipher truth table, and quantum circuit in a scrolling narrative.

| Route | Purpose |
| --- | --- |
| `/` | Main interactive simulation and explanation |
| `/_kit` | Component lab for controls, colors, tooltips, and telemetry |
| `/_scroll` | Alternate scrolling presentation demo |

Open the **Control dock** to change the input size, permutation, keys, shot count, or random seed. Select **Run simulation** after editing parameters.

- **Default** restores the project’s working three-bit example.
- **Random valid** searches for a permutation satisfying the exact Simon promise for the current size and key. Search can fail; the API limits it to 1,000 attempts.
- **Custom** accepts a comma-separated permutation containing every integer from `0` through `2^n - 1` exactly once.
- **Attacker view** hides displayed secrets until revealed. This is a presentation feature: the simulator still receives the keys.
- **Reset to project defaults** restores the initial configuration.

Changing the input size initializes the permutation to the identity. This generally does not satisfy the exact two-to-one promise for sizes above one bit; select a suitable permutation before interpreting the results as the ideal Simon experiment.

### Default experiment

| Parameter | Value |
| --- | --- |
| Input width `n` | `3` |
| Public permutation `P` | `[0, 2, 3, 5, 4, 1, 6, 7]` |
| First key `k1` | `101` binary / `5` decimal |
| Second key `k2` | `011` binary / `3` decimal |
| Shots | `4096` |
| Seed | `42` |
| Circuit qubits | `6` (`2n`) |

For this instance, the ideal measured outcomes are `000`, `010`, `101`, and `111`, each with probability `0.25`. Sampled frequencies fluctuate. With sufficient independent equations, the solver recovers `k1 = 101`, derives `k2 = 011`, and verifies all eight encryption outputs.

## Standalone Python demonstration

From the project root with the virtual environment activated:

```bash
python even_mansour_simon.py
```

The script runs 1,024 real Qiskit shots by default and presents eight numbered steps: the encryption problem, worked truth table, period proof, circuit, actual measurements, first-key recovery using XOR equations and substitution, second-key calculation, and complete ciphertext verification. It prefers measured strings `010` and `101` when present and adapts to other independent measurements. No matrix solution is displayed. The browser key-recovery walkthrough uses the same explanation generator. It also saves:

```text
outputs/simon_circuit.png
outputs/theory_vs_simulation.png
```

The script ends with `plt.show()`, which may open plot windows and wait for them to close. For a noninteractive run:

```bash
MPLBACKEND=Agg python even_mansour_simon.py --no-show
```

Use `--seed 7` to change the simulator seed or `--shots 2048` to change the shot count. The web app retains its editable 4,096-shot default. The example’s constants (`N`, `SHOTS`, `P`, `SECRET_K1`, and `SECRET_K2`) are at the top of `even_mansour_simon.py`. Its printed formatting and final verification message are tailored to the default three-bit example; use the API or core functions for general experiments. Output paths are relative to the working directory.

## How the algorithm works

### Cipher and hidden period

For an `n`-bit input `x`, public permutation `P`, and secret keys `k1` and `k2`, Even–Mansour encryption is:

```text
E(x) = P(x XOR k1) XOR k2
```

The simulator constructs:

```text
f(x) = E(x) XOR P(x)
     = P(x XOR k1) XOR P(x) XOR k2
```

This gives `f(x) = f(x XOR k1)`. Simon’s standard promise additionally requires a nonzero period and exactly two inputs per output. A permutation alone does not guarantee this: extra collisions can occur. `build_instance` checks bijectivity, periodicity, output multiplicities, and the number of distinct outputs, reporting `promise_ok` and failure reasons.

### Quantum circuit

The circuit uses an `n`-qubit input register and an `n`-qubit output register:

1. Initialize both registers to zero.
2. Apply Hadamard gates to the input register.
3. Apply reversible encryption and permutation lookup gates, XORing `f(x)` into the output register.
4. Apply Hadamard gates to the input register again.
5. Measure the input register with Qiskit’s `StatevectorSampler`.

Under the exact promise, each measured bitstring `y` satisfies:

```text
y · k1 = 0 mod 2
```

Qiskit measurement strings are interpreted with `int(bitstring, 2)`. The core uses `(y & k1).bit_count() % 2` for the binary inner product.

### Classical recovery

The shared `recovery_explanation.py` routine accepts only measurements, the public permutation, and known ciphertexts; it has no secret-key parameters. It selects independent equations by filtering possible bitstrings, explains variable isolation and substitution in ordinary XOR notation, and tries the remaining free bits. Exhaustive candidate checking independently confirms the explanation. The zero candidate is excluded under Simon’s nonzero-period promise. The existing GF(2) helper remains available internally for compatibility, but its technical steps are not shown in the key-recovery walkthrough.

Once `k1` is recovered, one known plaintext/ciphertext pair gives:

```text
k2 = E(0) XOR P(k1)
```

The implementation verifies the resulting keys against every entry in the generated cipher table. Insufficient independent measurements leave recovery unresolved rather than selecting an arbitrary candidate.

### Statistics and supporting experiments

- **Total variation distance:** discrepancy between sampled and ideal probabilities across all outcomes.
- **Chi-square statistic and p-value:** fit on the allowed support only; forbidden counts are excluded from this calculation, so inspect `support_ok` separately.
- **Success probability:** for `t` independent uniform samples in an `(n - 1)`-dimensional space, the full-rank probability is `product(1 - 2^(i - t), i = 0 ... n - 2)` when `t >= n - 1`, and zero otherwise.
- **Monte Carlo curve:** estimates full-rank probability from ideal samples; it does not repeatedly execute the quantum circuit.
- **Complexity curves:** illustrative query-growth curves for brute force, birthday search, Grover, and Simon, not measured runtime benchmarks.

## API reference

All POST bodies use JSON. Integer fields use JSON integers, keys are decimal integers, and `P` is an integer array. Request models reject extra fields and use strict validation.

| Method | Endpoint | Input | Result |
| --- | --- | --- | --- |
| GET | `/api/health` | None | Service status |
| GET | `/api/defaults` | None | Default experiment parameters |
| POST | `/api/instance` | Instance | Cipher/function tables, collision pairs, promise checks |
| POST | `/api/run` | Run | Counts, theory, statistics, sample sequence, circuit metrics, runtime |
| POST | `/api/solve` | Run | Measurements, elimination steps, candidates, recovered keys, verification |
| POST | `/api/stages` | Instance | Nonzero amplitudes at four circuit stages and interference information |
| GET | `/api/circuit.svg` | Query: `n`, comma-separated `P`, `k1`, `k2` | Circuit drawing as SVG |
| POST | `/api/success-curve` | Success | Theoretical and Monte Carlo success curves |
| GET | `/api/complexity` | Query: `n_max` (default/max `64`) | Query-growth series |
| GET | `/api/failure-cases` | None | Three illustrative promise failures and solver outcomes |
| POST | `/api/random-instance` | RandomInstance | Random instance satisfying the exact promise, or HTTP 503 |

### Request contracts

| Contract | Fields and bounds |
| --- | --- |
| Instance | `n`: 1–6; `P`: permutation of `0..2^n-1`; `k1`, `k2`: `0..2^n-1` |
| Run | Instance fields plus `shots`: 1–8192 (default 4096); `seed`: 0–4294967295 (default 42) |
| Success | `n`: 2–6; nonzero `k1`; `t_max`: 1–64 (default 16); `trials`: 1–10000 (default 4000); `seed`: same bounds, default 42 |
| RandomInstance | `n`: 1–6; optional nonzero `k1`; optional `seed` with the same bounds |

Instance validation permits zero `k1` and permutations that fail the Simon promise so that failure cases can be explored. Check `/api/instance` before assuming the ideal distribution applies.

### Example request

With the API running:

```bash
curl -sS http://localhost:8000/api/run \
  -H 'Content-Type: application/json' \
  -d '{"n":3,"P":[0,2,3,5,4,1,6,7],"k1":5,"k2":3,"shots":4096,"seed":42}'
```

Send the same body to `/api/solve` to inspect key recovery. `/api/run` and `/api/solve` each perform their own sampling call; use matching parameters and seeds for reproducible comparisons.

Validation errors return HTTP 422 with `error` and `detail` fields. Exhausted random searches return HTTP 503. Unexpected simulation failures return HTTP 500 with a generic explanation. See `/docs` for interactive request schemas.

## Project structure

```text
.
├── README.md
├── even_mansour_simon.py          # Standalone demonstration and plots
├── recovery_explanation.py        # Shared measurement-only recovery and explanation
├── simon_core.py                  # Cipher, circuit, sampling, GF(2), statistics
├── requirements.txt              # Python dependencies
├── server/
│   ├── main.py                   # FastAPI routes and SVG rendering
│   └── schemas.py                # Strict request validation
├── tests/
│   ├── test_core.py              # Simulator and algorithm tests
│   └── test_api.py               # API, validation, and rendering tests
├── web/
│   ├── package.json              # Frontend dependencies and commands
│   ├── package-lock.json         # Locked npm dependency tree
│   ├── vite.config.ts            # Development API proxy
│   └── src/
│       ├── main.tsx              # Entry point and route selection
│       ├── StoryApp.tsx          # Main narrative application
│       ├── App.tsx               # Component lab
│       ├── api/                  # API client and types
│       ├── state/                # Zustand simulation state
│       ├── sections/             # Narrative sections
│       ├── components/           # Controls and reusable UI
│       ├── charts/               # Theory/simulation visualization
│       ├── engine/               # Scrolling and visual effects
│       └── design/               # Design tokens and textures
├── outputs/                      # Generated plots (gitignored)
├── Final IA3 quantum  report.docx
└── Final IA3 quantum presentation.pptx
```

The frontend uses React 19, TypeScript, Vite, Zustand, GSAP, Lenis, and Framer Motion. Core simulation logic is shared by the CLI and API.

## Testing and building

Run the Python suite from the project root with the virtual environment activated:

```bash
python -m pytest -q
```

Additional tests check both reversible oracle gates on all 64 input/output basis states, all three independent measurement pairs for the teaching example, absent measurements, alternative keys, and the complete terminal demonstration. Tests cover the default instance, measured support, recovery, success probabilities, permutation search, promise failures, API validation, CORS, state stages, interference, and SVG output. API tests use an in-process client; a running Uvicorn process is not required.

Build the frontend from `web`:

```bash
npm run build
```

This runs TypeScript checking and creates static assets in `web/dist`. There is no frontend test script currently defined.

```bash
npm run preview
```

The preview command serves the built frontend locally. A deployed frontend still needs `/api` routed to the FastAPI service; static assets alone cannot execute simulations. Uvicorn does not currently serve `web/dist`. Configure the hosting server’s API proxy and SPA fallback when deploying.

## Limitations

- This is a small educational simulation, not an attack tool for production encryption. The backend knows the keys to construct the simulated encryption oracle and verify results.
- Simon’s advantage assumes coherent quantum access to the required oracles and a suitable promise. It does not imply the same attack is possible with ordinary classical API access to a cipher.
- The API limits circuit experiments to six input bits. Lookup construction and statevector simulation grow exponentially; the displayed linear Simon query curve is not the runtime scaling of this implementation.
- The solver enumerates nullspace candidates, which is suitable for these small experiments but is not a scalable general nullspace implementation.
- Periodicity alone does not establish the exact Simon promise. Extra collisions can produce a different distribution and ambiguous recovery. `support_ok` alone does not prove the promise.
- Too few shots, repeated measurements, or zero rows can leave the solver without enough independent equations.
- Random valid-instance search is bounded and is not guaranteed to succeed for every size, key, and seed. Changing the seed cannot fix mathematically impossible promise constraints.
- Most Python dependencies are unpinned; Qiskit is pinned. The repository does not provide a complete Python lockfile.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Frontend says it cannot reach the simulator | Start Uvicorn on port 8000 and check `/api/health`. Keep both terminals running. |
| `ModuleNotFoundError` | Activate `.venv`, install `requirements.txt`, and invoke tools with `python -m ...` to use that interpreter. |
| Uvicorn cannot import `server.main` | Run the command from the project root, not `web` or `server`. |
| `npm` is not found | Install Node.js with npm, then reopen the terminal. |
| Port already in use | Stop the existing process or choose another port. If the API port changes, update the target in `web/vite.config.ts`. |
| Browser shows HTTP 422 | Inspect the response detail; check integer types, permutation length/content, key ranges, and shot bounds. |
| Promise failed or recovery is ambiguous | Restore the default preset, inspect the instance checks, and increase shots if the promise holds but rank is insufficient. |
| Random valid preset fails | Try another seed or restore the default three-bit instance. Search is limited to 1,000 attempts. |
| Direct browser API calls encounter CORS errors | The API explicitly allows `http://localhost:5173`. Use the Vite `/api` proxy, or adjust CORS for your actual deployment origin. |
| CLI stays open after printing results | Close the Matplotlib windows, or run with `MPLBACKEND=Agg`. |
| SVG or plot rendering fails | Confirm Matplotlib and pylatexenc are installed in the same virtual environment as Qiskit. |

