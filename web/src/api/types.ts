export interface InstanceParams {n:number;P:number[];k1:number;k2:number}
export interface Defaults extends InstanceParams {shots:number;seed:number}
export interface RunResult {counts:Record<string,number>;theory:Record<string,number>;tvd:number;chi2:{stat:number;p_value:number};support_ok:boolean;circuit_stats:{depth:number;gate_counts:Record<string,number>;qubits:number};sequence:string[];runtime_ms:number}
