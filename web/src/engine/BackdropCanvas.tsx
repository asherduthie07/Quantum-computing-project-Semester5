import { useEffect, useRef } from 'react';
import { useReducedMotion } from '../design/motion';

// Keep the full-screen mesh in CSS. The canvas only paints lightweight particles.
export function BackdropCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    const canvas = ref.current!, ctx = canvas.getContext('2d')!;
    let frame = 0, w = 0, h = 0, last = 0, time = 0, colorAt = 0;
    let colors = ['190', '263', '225'], active = !document.hidden, slowFrames = 0;
    let count = matchMedia('(max-width:767px)').matches ? 24 : 72;
    const points = Array.from({ length: count }, (_, i) => ({
      x: Math.random(), y: Math.random(), phase: i * 2.4, tier: i % 3,
      px: 0, py: 0,
    }));
    let targetX = 0, targetY = 0, mx = 0, my = 0;
    const resize = () => {
      w = innerWidth; h = innerHeight;
      const dpr = Math.min(devicePixelRatio, 1.5);
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const pointer = (e: PointerEvent) => {
      targetX = (e.clientX / w - .5) * 12;
      targetY = (e.clientY / h - .5) * 12;
    };
    const draw = (now: number) => {
      frame = 0;
      if (!active || reduced) return;
      const delta = last ? now - last : 16.7;
      last = now; time += Math.min(delta, 50) / 1000;
      // Reduce work when frames are late, rather than forcing a choppy 30fps cap.
      if (delta > 24) slowFrames++;
      else slowFrames = Math.max(0, slowFrames - 1);
      if (slowFrames > 24 && count > 24) { count -= 12; slowFrames = 0; }
      if (now - colorAt > 200) {
        const css = getComputedStyle(document.documentElement);
        colors = ['a', 'b', 'c'].map(k => css.getPropertyValue(`--hue-${k}`).trim());
        colorAt = now;
      }
      const ease = 1 - Math.exp(-delta / 90);
      mx += (targetX - mx) * ease; my += (targetY - my) * ease;
      ctx.clearRect(0, 0, w, h);
      const scroll = window.scrollY;
      for (let i = 0; i < count; i++) {
        const p = points[i];
        p.px = p.x * w + Math.sin(time * .12 + p.phase) * 30 + mx * (p.tier + 1);
        p.py = ((p.y * (h + 200) + Math.cos(time * .1 + p.phase) * 25 - scroll * [.15, .3, .5][p.tier] + my * (p.tier + 1)) % (h + 200) + h + 200) % (h + 200) - 100;
      }
      for (let tier = 0; tier < 3; tier++) {
        ctx.strokeStyle = `hsla(${colors[tier]},70%,70%,.07)`;
        ctx.beginPath();
        for (let i = tier; i < count; i += 3) {
          const p = points[i];
          for (let j = i + 3; j < count; j += 3) {
            const q = points[j], dx = p.px - q.px, dy = p.py - q.py;
            if (dx * dx + dy * dy < 14400) { ctx.moveTo(p.px, p.py); ctx.lineTo(q.px, q.py); }
          }
        }
        ctx.stroke();
        ctx.fillStyle = `hsla(${colors[tier]},90%,75%,.6)`;
        ctx.beginPath();
        for (let i = tier; i < count; i += 3) {
          const p = points[i]; ctx.moveTo(p.px + 1.5, p.py); ctx.arc(p.px, p.py, 1.5, 0, Math.PI * 2);
        }
        ctx.fill();
        ctx.font = `${12 + tier * 3}px 'JetBrains Mono'`;
        ctx.fillStyle = `hsla(${colors[tier]},70%,75%,.12)`;
        for (let i = tier; i < count; i += 18) {
          const p = points[i]; ctx.fillText((i % 8).toString(2).padStart(3, '0'), p.px + 10, p.py);
        }
      }
      frame = requestAnimationFrame(draw);
    };
    const visibility = () => {
      active = !document.hidden; cancelAnimationFrame(frame); last = 0;
      if (active && !reduced) frame = requestAnimationFrame(draw);
    };
    resize(); visibility();
    window.addEventListener('resize', resize);
    if (!reduced) window.addEventListener('pointermove', pointer, { passive: true });
    document.addEventListener('visibilitychange', visibility);
    return () => {
      cancelAnimationFrame(frame); window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', pointer);
      document.removeEventListener('visibilitychange', visibility);
    };
  }, [reduced]);
  return <><div className="backdrop-mesh" aria-hidden="true"/><canvas ref={ref} className="backdrop-canvas" aria-hidden="true"/></>;
}
