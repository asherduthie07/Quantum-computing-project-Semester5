import { useEffect, useState } from 'react';
import { useSim } from '../state/useSim';
import { useReducedMotion } from '../design/motion';
export function SecretBits({value}:{value:number}){const {params,attackerView,revealKeys}=useSim(),reduced=useReducedMotion(),[scramble,setScramble]=useState<string|null>(null);useEffect(()=>{if(!revealKeys||reduced){setScramble(null);return}let tick=0;const timer=setInterval(()=>{tick++;setScramble(Array.from({length:params?.n??3},()=>Math.random()>.5?'1':'0').join(''));if(tick===10){clearInterval(timer);setScramble(null)}},45);return()=>clearInterval(timer)},[revealKeys,reduced,params?.n]);return <span className={`mono secret ${revealKeys?'unmask':''}`}>{attackerView&&!revealKeys?'???':scramble??value.toString(2).padStart(params?.n??3,'0')}</span>}
