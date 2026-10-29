import { useEffect, useRef, type HTMLAttributes } from 'react';
import clsx from 'clsx';
import { useReducedMotion } from '../design/motion';

export function Card({ className, children, ...props }: HTMLAttributes<HTMLElement>) {
  const reduced = useReducedMotion();
  const frame = useRef(0);
  const bounds = useRef<DOMRect | null>(null);
  useEffect(() => () => cancelAnimationFrame(frame.current), []);
  return <article {...props} className={clsx('card glass', className)}
    onPointerEnter={e => { bounds.current = e.currentTarget.getBoundingClientRect(); }}
    onPointerMove={e => {
      const r = bounds.current;
      // Data tables and pinned panels should stay stable while being read.
      if (reduced || e.pointerType === 'touch' || !r || r.width > 550 || r.height > 400) return;
      const element = e.currentTarget;
      const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      cancelAnimationFrame(frame.current);
      frame.current = requestAnimationFrame(() => {
        element.style.transform = `perspective(1000px) rotateX(${(.5-y)*4}deg) rotateY(${(x-.5)*4}deg)`;
      });
    }}
    onPointerLeave={e => {
      cancelAnimationFrame(frame.current); bounds.current = null;
      e.currentTarget.style.transform = '';
    }}>{children}</article>;
}
