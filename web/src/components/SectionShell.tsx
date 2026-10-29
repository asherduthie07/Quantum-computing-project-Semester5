import type { ReactNode } from 'react';
import { palettes } from '../design/motion';
export function SectionShell({id,title,eyebrow,subhead,children,palette='Hero'}:{id:string;title:string;eyebrow:string;subhead:string;children:ReactNode;palette?:keyof typeof palettes}){return <section id={id} data-palette={palette}><span className="eyebrow">{eyebrow}</span><h2>{title}</h2><p>{subhead}</p>{children}</section>}
