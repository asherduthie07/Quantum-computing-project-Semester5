import { useId } from 'react';
import type { RunResult } from '../api/types';

/** Display-only normalization; the backend supplies counts and theoretical probabilities. */
export function TheorySimulation({ result }: { result: RunResult }) {
  const titleId = useId(), descriptionId = useId();
  const outcomes = Object.keys(result.theory).sort();
  const total = Object.values(result.counts).reduce((sum, count) => sum + count, 0);
  const rows = outcomes.map(outcome => ({
    outcome, theory: result.theory[outcome], count: result.counts[outcome] ?? 0,
    simulated: total ? (result.counts[outcome] ?? 0) / total : 0,
  }));
  const maximum = Math.max(...rows.flatMap(row => [row.theory, row.simulated]));
  const upper = Math.min(1, Math.max(.1, Math.ceil(maximum * 10) / 10));
  const width = Math.max(720, outcomes.length * 76 + 100);
  const height = 350, left = 65, right = 25, top = 30, bottom = 65;
  const plotHeight = height - top - bottom, slot = (width - left - right) / outcomes.length;
  const barWidth = Math.min(27, slot * .3);
  const y = (probability: number) => top + plotHeight * (1 - probability / upper);
  return <>
    <div className="chart-legend" aria-label="Chart legend">
      <span><i className="theory-swatch"/>Theory</span>
      <span><i className="simulation-swatch"/>Simulation</span>
      <span className="muted">Probability · {total.toLocaleString()} measured shots</span>
    </div>
    <div className="histogram-scroll" data-lenis-prevent tabIndex={0} role="region" aria-label="Theory versus simulation chart; scroll horizontally for larger instances">
      <svg className="histogram" viewBox={`0 0 ${width} ${height}`} style={{ minWidth: width }} role="img" aria-labelledby={`${titleId} ${descriptionId}`}>
        <title id={titleId}>Theory versus simulation probability by measured outcome</title>
        <desc id={descriptionId}>Violet bars are theoretical probabilities. Cyan bars are observed counts divided by the total shots. Red zero markers identify outcomes forbidden by the ideal theory. Exact values are in the table below.</desc>
        {Array.from({ length: 5 }, (_, i) => upper * i / 4).map(tick => <g key={tick}>
          <line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} stroke="var(--card-border)"/>
          <text x={left - 12} y={y(tick) + 4} textAnchor="end" className="chart-axis">{(tick * 100).toFixed(1)}%</text>
        </g>)}
        {rows.map((row, index) => {
          const center = left + slot * (index + .5);
          return <g key={row.outcome}>
            <title>{row.outcome}: theory {(row.theory * 100).toFixed(2)}%, simulation {(row.simulated * 100).toFixed(2)}%, {row.count} counts</title>
            <rect x={center - barWidth - 2} y={y(row.theory)} width={barWidth} height={plotHeight * row.theory / upper} rx="3" fill="var(--theory)"/>
            <rect x={center + 2} y={y(row.simulated)} width={barWidth} height={plotHeight * row.simulated / upper} rx="3" fill="var(--quantum)"/>
            {row.theory === 0 && <text x={center - barWidth / 2 - 2} y={y(0) - 8} textAnchor="middle" fill="var(--fail)" className="mono" fontSize="12">0</text>}
            <text x={center} y={height - bottom + 24} textAnchor="middle" className="chart-axis">{row.outcome}</text>
          </g>;
        })}
        <text x={width / 2} y={height - 8} textAnchor="middle" className="chart-axis">Measured x-register bitstring</text>
      </svg>
    </div>
    <details className="chart-data">
      <summary>View exact probabilities and counts</summary>
      <div className="histogram-scroll" data-lenis-prevent>
        <table className="truth-table mono"><caption>Values from the latest completed simulation</caption>
          <thead><tr><th scope="col">Outcome</th><th scope="col">Theory</th><th scope="col">Simulation</th><th scope="col">Count</th></tr></thead>
          <tbody>{rows.map(row => <tr key={row.outcome}><th scope="row">{row.outcome}</th><td>{(row.theory * 100).toFixed(3)}%</td><td>{(row.simulated * 100).toFixed(3)}%</td><td>{row.count.toLocaleString()}</td></tr>)}</tbody>
        </table>
      </div>
    </details>
  </>;
}
