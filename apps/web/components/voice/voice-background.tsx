'use client';

import { useEffect, useRef } from 'react';

export function VoiceBackground() {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Generate small random interactive particles in background
        const container = containerRef.current;
        if (!container) return;

        const count = 30;
        const particles: HTMLSpanElement[] = [];

        for (let i = 0; i < count; i++) {
            const p = document.createElement('span');
            p.className = 'absolute rounded-full bg-[#00FF9D] opacity-10 pointer-events-none transition-transform duration-1000';
            const size = Math.random() * 2 + 1;
            p.style.width = `${size}px`;
            p.style.height = `${size}px`;
            p.style.left = `${Math.random() * 100}%`;
            p.style.top = `${Math.random() * 100}%`;

            // Floating animation speed
            p.style.transition = 'all 20s linear';

            container.appendChild(p);
            particles.push(p);
        }

        const interval = setInterval(() => {
            particles.forEach((p) => {
                p.style.left = `${Math.random() * 100}%`;
                p.style.top = `${Math.random() * 100}%`;
            });
        }, 15000);

        return () => {
            clearInterval(interval);
            particles.forEach((p) => p.remove());
        };
    }, []);

    return (
        <div
            ref={containerRef}
            className="absolute inset-0 -z-50 overflow-hidden bg-[#05070A] pointer-events-none"
        >
            {/* Moving Cyberpunk Grid Background */}
            <div
                className="absolute inset-0 opacity-15"
                style={{
                    backgroundImage: `
            linear-gradient(rgba(0, 255, 157, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 157, 0.08) 1px, transparent 1px)
          `,
                    backgroundSize: '40px 40px',
                    maskImage: 'radial-gradient(ellipse at center, black, transparent 80%)',
                    WebkitMaskImage: 'radial-gradient(ellipse at center, black, transparent 80%)',
                }}
            />

            {/* Hexagonal overlay layer */}
            <div
                className="absolute inset-0 opacity-5"
                style={{
                    backgroundImage: `
            radial-gradient(circle at 20% 30%, rgba(0, 229, 255, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(136, 255, 204, 0.1) 0%, transparent 60%)
          `
                }}
            />

            {/* Futuristic Scanlines */}
            <div
                className="absolute inset-0 pointer-events-none opacity-[0.03]"
                style={{
                    backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
                    backgroundSize: '100% 4px, 6px 100%',
                }}
            />

            {/* Light Blooms / Radars Glow */}
            <div className="absolute top-[-10%] left-[20%] w-[45%] h-[35%] rounded-full bg-[#00FF9D] opacity-[0.025] blur-[120px] animate-pulse" />
            <div className="absolute bottom-[-10%] right-[10%] w-[55%] h-[40%] rounded-full bg-[#00E5FF] opacity-[0.02] blur-[150px]" />
        </div>
    );
}
