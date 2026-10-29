import type { Defaults, RunResult } from './types';
async function request<T>(path:string,body?:unknown):Promise<T>{const response=await fetch(`/api/${path}`,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});if(!response.ok)throw new Error('The simulation service is unavailable. Please retry.');return response.json()}
export const api={request,defaults:()=>request<Defaults>('defaults'),run:(params:Defaults)=>request<RunResult>('run',params)};
