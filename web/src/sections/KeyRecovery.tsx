import { useSim } from '../state/useSim';
import { SectionShell } from '../components/SectionShell';
import { Card } from '../components/Card';

export default function KeyRecovery() {
  const {params: p, instance, solved, loading} = useSim();
  if (!p) return null;
  const bits = (v: number) => v.toString(2).padStart(p.n, '0');
  const first = solved?.recovered_k1;
  const second = solved?.recovered_k2;
  return <SectionShell id="recovery" eyebrow="04 / Recovering the keys" title="From measurements to both keys." subhead="Every calculation below uses your current simulation. Edit the control dock and run again to follow a new instance.">
    {!instance || !solved || loading ? <p role="status">{loading ? 'Calculating the recovery steps…' : 'Run the simulation to calculate the keys for these inputs.'}</p> : <div className="recovery-steps">
      <Card><h3>1–3. Recover the first key with equations and substitution</h3>
        <p>Use the actual measurements to discover the unknown bits. All bitstrings are binary; XOR is addition modulo 2.</p>
        <p className="mono">n = {p.n} · shots = {p.shots} · seed = {p.seed}</p>
        {!instance.promise_ok && <p className="error">The exact Simon promise failed: {instance.reasons.join('. ')}. A unique nonzero period is not guaranteed.</p>}
        {solved.explanation?.map((line: string, i: number) => <p className="mono recovery-wrap" key={i}>{line}</p>)}
      </Card>
      <Card><h3>4. Calculate the second key</h3><p>Use the public permutation and the known plaintext/ciphertext pair at x = 0. Rearrange E(x) = P(x ⊕ k₁) ⊕ k₂:</p><p className="mono">k₂ = E(0) ⊕ P(k₁)</p>
        {first != null && second != null ? <><p className="mono">E({bits(0)}) = {bits(instance.E[0])}</p><p className="mono">{bits(0)} ⊕ recovered k₁ = {bits(0)} ⊕ {bits(first)} = {bits(first)}</p><p className="mono">P({bits(first)}) = P[{first}] = {bits(p.P[first])}</p><pre className="recovery-xor">{`  ${bits(instance.E[0])}  E(0)\n⊕ ${bits(p.P[first])}  P(k₁)\n${'─'.repeat(p.n+2)}\n  ${bits(second)}  k₂`}</pre><p className="recovery-answer mono">k₂ = {bits(second)}₂ = {second}</p></> : <p>Waiting for a unique first-key candidate.</p>}
      </Card>
      <Card><h3>5. Verify both keys on every input</h3><p>Recalculate P(x ⊕ recovered k₁) ⊕ recovered k₂ and compare it with the original E(x). All values below are binary.</p>
        {first != null && second != null ? <><p className={solved.all_match ? 'success' : 'fail'}>{solved.verification.filter((v: {match: boolean}) => v.match).length} / {p.P.length} outputs match. {solved.all_match ? 'The recovered keys reproduce the cipher table.' : 'Verification failed; do not accept these candidate keys.'}</p><div className="recovery-table" data-lenis-prevent><table className="truth-table mono"><thead><tr><th>x</th><th>x ⊕ k₁</th><th>P(x ⊕ k₁) ⊕ k₂</th><th>E(x)</th><th>Match</th></tr></thead><tbody>{solved.verification.map((v: {x: number; original: number; recovered: number; match: boolean}) => <tr key={v.x}><td>{bits(v.x)}</td><td>{bits(v.x)} ⊕ {bits(first)} = {bits(v.x ^ first)}</td><td>{bits(p.P[v.x ^ first])} ⊕ {bits(second)} = {bits(v.recovered)}</td><td>{bits(v.original)}</td><td className={v.match ? 'success' : 'fail'}>{v.match ? 'Yes' : 'No'}</td></tr>)}</tbody></table></div></> : <p>Verification becomes available after both keys are recovered.</p>}
        <p className="muted">This walkthrough shows derived keys, including in attacker view. The simulator uses the supplied secrets to build its oracle and original cipher table; recovery uses measured equations and E(0).</p>
      </Card>
    </div>}
  </SectionShell>;
}
