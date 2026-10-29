import { useSim } from '../state/useSim';
import { SectionShell } from '../components/SectionShell';
import { TheorySimulation } from '../charts/TheorySimulation';

export default function Measurement() {
  const result = useSim(state => state.result);
  const instance = useSim(state => state.instance);
  const loading = useSim(state => state.loading);
  const error = useSim(state => state.error);
  const run = useSim(state => state.run);
  return <SectionShell id="measurement" palette="Measurement" eyebrow="Live simulation / theory versus evidence"
    title="The prediction. The measured reality."
    subhead="Compare the ideal quantum distribution with the outcomes of your latest simulation.">
    <div className="comparison-panel" aria-busy={loading}>
      {loading && <p role="status">Running simulation… {result ? 'Showing the previous completed run until the new result arrives.' : ''}</p>}
      {result ? <>
        {instance && !instance.promise_ok && <p className="error" role="status">This instance fails Simon’s promise. The violet bars show the ideal period model; the sampled distribution may differ.</p>}
        <TheorySimulation result={result}/>
        <div className="comparison-metrics">
          <div><span>Total variation distance</span><strong className="mono quantum">{result.tvd.toFixed(5)}</strong></div>
          <div><span>Chi-square p-value</span><strong className="mono theory">{result.chi2.p_value.toFixed(5)}</strong></div>
          <div><span>All shots inside allowed support</span><strong className={`mono ${result.support_ok ? 'success' : 'fail'}`}>{result.support_ok ? 'YES' : 'NO'}</strong></div>
          <div><span>Simulation runtime</span><strong className="mono">{result.runtime_ms.toFixed(1)} ms</strong></div>
        </div>
        <p className="code-note">Finite samples fluctuate around the theoretical probabilities. The chi-square test uses the allowed support only. Qiskit count keys are measured x-register strings, interpreted as int(bitstring, 2) for GF(2) dot products.</p>
      </> : !loading && <p>Run the simulation to see its probability distribution.</p>}
      {error && <p className="error" role="alert">{error} <button className="term" disabled={loading} onClick={() => void run()}>Retry simulation</button></p>}
    </div>
  </SectionShell>;
}
