import { useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import Measurement from './sections/Measurement';
import TruthTable from './sections/TruthTable';
import Circuit from './sections/Circuit';
import KeyRecovery from './sections/KeyRecovery';
import Hero from './sections/Hero';
import Problem from './sections/Problem';
import { ControlDock } from './components/ControlDock';
import { BackdropCanvas } from './engine/BackdropCanvas';
import { MidLayer } from './engine/MidLayer';
import { Cursor } from './engine/Cursor';
import { useSim } from './state/useSim';
import { SecretBits } from './components/SecretBits';
import { palettes, useReducedMotion } from './design/motion';
gsap.registerPlugin(ScrollTrigger);
export default function StoryApp(){const s=useSim(),reduced=useReducedMotion();useEffect(()=>{document.title='Simon Observatory · Breaking a cipher';void s.load()},[]);useEffect(()=>{const lenis=reduced?null:new Lenis({lerp:.14,syncTouch:false});const tick=(t:number)=>lenis?.raf(t*1000);lenis?.on('scroll',ScrollTrigger.update);if(lenis)gsap.ticker.add(tick);const ctx=gsap.context(()=>{(['Hero','Measurement','Problem','TruthTable','Circuit'] as const).forEach(name=>ScrollTrigger.create({trigger:`#${name.toLowerCase()}`,start:'top center',end:'bottom center',onToggle:self=>{if(self.isActive){const [a,b,c]=palettes[name];gsap.to(document.documentElement,{'--hue-a':a,'--hue-b':b,'--hue-c':c,duration:reduced?0:1.2,overwrite:true})}}}));if(!reduced)gsap.utils.toArray<HTMLElement>('.story-reveal,.proof-terms>span').forEach(el=>gsap.from(el,{opacity:0,y:40,duration:.8,ease:'power3.out',scrollTrigger:{trigger:el,start:'top 90%',once:true}}))});ScrollTrigger.refresh();return()=>{ctx.revert();lenis?.destroy();gsap.ticker.remove(tick);gsap.killTweensOf(document.documentElement)}},[reduced]);useEffect(()=>{const frame=requestAnimationFrame(()=>ScrollTrigger.refresh());return()=>cancelAnimationFrame(frame)},[!!s.instance]);return <div className="scroll-demo"><a className="skip" href="#problem">Skip to the problem</a><BackdropCanvas/><MidLayer/><Cursor/><div className="grain" aria-hidden="true"/><nav className="story-nav" aria-label="Simulation overview"><a href="#hero">⊕ SIMON</a><div className="live-chips mono">{s.result&&s.params&&<><span>{s.result.circuit_stats.qubits} qubits</span><span>{s.params.shots} shots</span><span>Promise {s.instance?.promise_ok?'OK':'failed'}</span><span>k₁ <SecretBits value={s.params.k1}/></span><span>k₂ <SecretBits value={s.params.k2}/></span><span>{s.solved?.verification.filter((r:any)=>r.match).length}/{s.solved?.verification.length} verified</span></>}</div></nav><nav className="progress-rail" aria-label="Story chapters"><a href="#hero" aria-label="Hero"><span/><b>Hero</b></a><a href="#measurement" aria-label="Theory versus simulation"><span/><b>Results</b></a><a href="#problem" aria-label="Problem"><span/><b>Problem</b></a><a href="#truthtable" aria-label="Truth table"><span/><b>Truth table</b></a><a href="#circuit" aria-label="Circuit"><span/><b>Circuit</b></a><a href="#recovery" aria-label="Key recovery calculations"><span/><b>Key recovery</b></a></nav><main className="story-content"><Hero/><Measurement/><Problem/><TruthTable/><Circuit/><KeyRecovery/>{s.error&&<div className="error" role="alert">{s.error}<button onClick={()=>void s.run()}>Retry</button></div>}<footer><span>EVEN–MANSOUR × SIMON</span><a href="/_kit">Component lab ↗</a></footer></main><ControlDock/></div>}
