'use client';

import { useEffect, useState } from 'react';
import { GlassPanel } from './GlassPanel';

type TelemetryProps = {
    isRecording: boolean;
    hasSession: boolean;
};

export function TelemetryPanel({ isRecording, hasSession }: TelemetryProps) {
    // Animated telemetry placeholders
    const [cpuLoad, setCpuLoad] = useState(12);
    const [gpuLoad, setGpuLoad] = useState(5);
    const [ramFootprint, setRamFootprint] = useState(4.2);
    const [networkPing, setNetworkPing] = useState(120);

    useEffect(() => {
        const interval = setInterval(() => {
            setCpuLoad((prev) => {
                const delta = Math.random() * 6 - 3;
                const target = isRecording ? 28 : 12;
                return Math.max(2, Math.min(99, Math.round(prev + (target - prev) * 0.15 + delta)));
            });
            setGpuLoad((prev) => {
                const delta = Math.random() * 4 - 2;
                const target = isRecording ? 18 : 6;
                return Math.max(1, Math.min(99, Math.round(prev + (target - prev) * 0.12 + delta)));
            });
            setRamFootprint((prev) => {
                const delta = Math.random() * 0.2 - 0.1;
                const target = hasSession ? 5.8 : 4.1;
                return Math.max(1.0, Math.min(16.0, parseFloat((prev + (target - prev) * 0.05 + delta).toFixed(2))));
            });
            setNetworkPing((prev) => {
                const delta = Math.random() * 12 - 6;
                const target = hasSession ? 115 : 0;
                if (!hasSession) return 0;
                return Math.max(10, Math.min(999, Math.round(prev + delta)));
            });
        }, 2000);

        return () => clearInterval(interval);
    }, [isRecording, hasSession]);

    const metrics = [
        { label: 'Voice Confidence', value: hasSession ? (isRecording ? '94%' : '98%') : 'N/A', status: hasSession ? 'ok' : 'idle' },
        { label: 'Noise Floor', value: isRecording ? '-42.6 dB' : '-64.1 dB', status: isRecording ? 'warn' : 'ok' },
        { label: 'Mic Stream Gain', value: isRecording ? '1.0x (Auto)' : '0.0x (Muted)', status: isRecording ? 'ok' : 'idle' },
        { label: 'Aether API Latency', value: networkPing > 0 ? `${networkPing} ms` : 'N/A', status: hasSession ? 'ok' : 'idle' },
        { label: 'Neural CPU Load', value: `${cpuLoad}%`, status: cpuLoad > 75 ? 'error' : cpuLoad > 40 ? 'warn' : 'ok' },
        { label: 'GPU Command Core', value: `${gpuLoad}%`, status: gpuLoad > 70 ? 'error' : 'ok' },
        { label: 'System RAM Used', value: `${ramFootprint} GB`, status: 'ok' },
        { label: 'Websocket Status', value: hasSession ? 'CONNECTED' : 'DISCONNECTED', status: hasSession ? 'ok' : 'error' },
    ];

    return (
        <GlassPanel glowColor="rgba(0, 217, 255, 0.08)" className="h-full flex flex-col justify-between">
            <div>
                <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#00D9FF] border-b border-[rgba(0,217,255,0.12)] pb-3 mb-4.5 font-mono">
                    SYSTEM TELEMETRY
                </h3>

                <div className="grid grid-cols-2 gap-4">
                    {metrics.map((item, idx) => (
                        <div
                            key={idx}
                            className="rounded-xl border border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.015)] p-4 relative space-y-1.5 transition-all duration-300 hover:border-[rgba(0,217,255,0.15)] hover:bg-[rgba(255,255,255,0.03)]"
                        >
                            <p className="text-[9px] uppercase font-bold text-slate-450 tracking-widest font-mono">
                                {item.label}
                            </p>
                            <div className="flex justify-between items-baseline">
                                <span className="text-xs font-black font-mono text-white tracking-wide">
                                    {item.value}
                                </span>
                                <span
                                    className={`w-2 h-2 rounded-full ${item.status === 'ok' ? 'bg-[#00FF9D] shadow-[0_0_8px_#00FF9D]' :
                                            item.status === 'warn' ? 'bg-[#FFD54F] shadow-[0_0_8px_#FFD54F]' :
                                                item.status === 'error' ? 'bg-[#FF5252] shadow-[0_0_8px_#FF5252] animate-pulse' :
                                                    'bg-slate-750'
                                        }`}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mt-6 rounded-xl border border-[rgba(0,255,157,0.12)] bg-[rgba(0,255,157,0.01)] p-4 text-[9px] font-mono flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-[#00FF9D] rounded-full animate-pulse" />
                    AETHER_CORE: SHIELDED
                </span>
                <span>NODE v18_QUANTUM</span>
            </div>
        </GlassPanel>
    );
}
