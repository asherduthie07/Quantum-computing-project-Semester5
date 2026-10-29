import { Tooltip } from './Tooltip';
export type Role='secret'|'quantum'|'theory'|'success'|'fail'|'add'|'cancel';
export function BitString({value,role='quantum'}:{value:string;role?:Role}){const decimal=parseInt(value,2),parity=[...value].reduce((s,b)=>s+Number(b),0)%2;return <Tooltip text={`Decimal ${decimal}. Bit parity: ${parity ? 'odd':'even'}. Measured x-register strings use int(bitstring, 2) for GF(2) dot products.`}><span className="bitstring" aria-label={`${value}, decimal ${decimal}`}>{[...value].map((b,i)=><span key={i} className={role}>{b}</span>)}</span></Tooltip>}
