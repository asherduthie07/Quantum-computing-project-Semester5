import { CountUp } from './CountUp';
export function Stat({label,value,unit='',role='quantum'}:{label:string;value:number;unit?:string;role?:string}){return <div className="stat"><div className={`stat-value ${role}`}><CountUp value={value}/><span style={{fontSize:'.85rem',marginLeft:6}}>{unit}</span></div><div className="stat-label">{label}</div></div>}
