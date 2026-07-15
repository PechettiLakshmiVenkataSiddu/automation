'use client';

import { useEffect, useState } from 'react';

type SystemHeaderProps = {
    sessionId: string | null;
    busy: boolean;
};

export function SystemHeader({ sessionId, busy }: SystemHeaderProps) {
    const [timeStr, setTimeStr] = useState('');

    useEffect(() => {
        const updateTime = () => {
            const d = new Date();
            setTimeStr(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
        };
        updateTime();
        const interval = setInterval(updateTime, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <header className="w-full border-b border-[rgba(0,255,157,0.15)] bg-[rgba(11,17,24,0.45)] backdrop-blur-md px-8 py-5 flex flex-col md:flex-row justify-between items-center gap-6 z-20 sticky top-0">
            {/* Left side: Brand Logo / Workspace Title */}
            <div className="flex items-center gap-4.5">
                <div className="w-11 h-11 border border-[#00FF9D] rounded-xl flex items-center justify-center relative shadow-[0_0_12px_rgba(0,255,157,0.22)] bg-[rgba(0,255,157,0.03)]">
                    <span className="text-lg font-black font-mono text-[#00FF9D] tracking-tighter">Æ</span>
                    <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-[#00FF9D] rounded-full animate-pulse shadow-[0_0_8px_#00FF9D]" />
                </div>
                <div>
                    <div className="flex items-center gap-2">
                        <h1 className="text-sm font-black tracking-[0.25em] font-mono text-white uppercase">
                            AETHER OS
                        </h1>
                        <span className="px-1.5 py-0.5 rounded border border-[#00D9FF] bg-[rgba(0,217,255,0.05)] text-[8px] font-mono font-bold text-[#00D9FF] tracking-wider">
                            WS_VOICE
                        </span>
                    </div>
                    <p className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">
                        Neural Command Interface: ACTIVE
                    </p>
                </div>
            </div>

            {/* Center: Live Core Details */}
            <div className="flex items-center gap-9 font-mono text-[10px] text-slate-450 tracking-wider">
                <div className="flex flex-col gap-1">
                    <span className="text-[8px] uppercase font-bold text-slate-500">Active Session</span>
                    <span className="text-white font-bold font-mono">
                        {sessionId ? `${sessionId.slice(0, 18)}...` : 'NO_ACTIVE_SESSION'}
                    </span>
                </div>

                <div className="flex flex-col gap-1">
                    <span className="text-[8px] uppercase font-bold text-slate-500">Quantum Link</span>
                    <span className="text-[#00D9FF] font-bold">SECURE AES-256</span>
                </div>

                <div className="flex flex-col gap-1">
                    <span className="text-[8px] uppercase font-bold text-slate-500">Core Engine</span>
                    <span className="text-[#79FFE8] font-bold">AETHER-V3-ALPHA</span>
                </div>
            </div>

            {/* Right side: Telemetry Gauges */}
            <div className="flex items-center gap-5 font-mono text-xs text-slate-400">
                <div className="flex items-center gap-2.5 border border-[rgba(0,255,157,0.15)] bg-[rgba(0,255,157,0.02)] rounded-lg px-4 py-2">
                    <span className="flex h-2 w-2 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00FF9D] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00FF9D]"></span>
                    </span>
                    <span className="text-[10px] font-bold text-[#00FF9D] tracking-widest uppercase">
                        {busy ? 'ENGINE_THINKING' : 'SYS_STANDBY'}
                    </span>
                </div>

                <div className="text-[10px] font-bold px-4 py-2 border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.01)] rounded-lg text-slate-350 tracking-widest uppercase">
                    CLOCK: {timeStr}
                </div>
            </div>
        </header>
    );
}
