'use client';

type SystemStatusProps = {
    isRecording: boolean;
    hasSession: boolean;
};

export function VoiceSystemStatus({ isRecording, hasSession }: SystemStatusProps) {
    // Metric variables
    const sampleRate = '16.0 kHz';
    const noiseLevel = isRecording ? '-42.8 dB' : '-65.4 dB';
    const confidence = hasSession ? (isRecording ? '94.2%' : '98.5%') : '--';
    const networkLatency = hasSession ? '124 ms' : '--';

    const metrics = [
        { label: 'Voice Engine', value: 'ONLINE', status: 'ok' },
        { label: 'Mic Stream', value: isRecording ? 'ACTIVE' : 'STANDBY', status: isRecording ? 'active' : 'warn' },
        { label: 'Confidence Score', value: confidence, status: hasSession ? 'ok' : 'idle' },
        { label: 'Noise Floor', value: noiseLevel, status: isRecording ? 'warn' : 'ok' },
        { label: 'Sample Rate', value: sampleRate, status: 'ok' },
        { label: 'Core Latency', value: networkLatency, status: hasSession ? 'ok' : 'idle' },
    ];

    return (
        <div className="rounded-xl border border-[rgba(0,255,157,0.18)] bg-[rgba(5,7,10,0.65)] backdrop-blur-md p-5 shadow-lg relative overflow-hidden space-y-4">
            <div className="absolute top-0 left-0 w-16 h-[2px] bg-gradient-to-r from-[#00FF9D] to-transparent" />
            <div className="absolute top-0 left-0 w-[2px] h-16 bg-gradient-to-b from-[#00FF9D] to-transparent" />

            <div className="flex justify-between items-center border-b border-[rgba(0,255,157,0.1)] pb-2.5">
                <h3 className="text-xs uppercase font-extrabold tracking-[0.2em] text-[#00FF9D]">
                    SYSTEM MONITOR MODULE
                </h3>
                <span className="text-[10px] font-mono text-slate-450 tracking-wider">SECURE LINK</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {metrics.map((item, idx) => (
                    <div
                        key={idx}
                        className="rounded-lg border border-[rgba(255,255,255,0.03)] bg-[rgba(255,255,255,0.015)] p-3 relative space-y-1.5 transition-all duration-300 hover:border-[rgba(0,255,157,0.12)] hover:bg-[rgba(255,255,255,0.03)]"
                    >
                        <p className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">{item.label}</p>
                        <div className="flex justify-between items-baseline">
                            <span className="text-sm font-black font-mono text-white tracking-wide">
                                {item.value}
                            </span>
                            <span
                                className={`w-1.5 h-1.5 rounded-full ${item.status === 'ok' ? 'bg-[#00FF9D] shadow-[0_0_6px_#00FF9D]' :
                                        item.status === 'active' ? 'bg-[#00E5FF] shadow-[0_0_6px_#00E5FF] animate-ping' :
                                            item.status === 'warn' ? 'bg-[#FFD93D] shadow-[0_0_6px_#FFD93D]' :
                                                'bg-slate-700'
                                    }`}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <div className="rounded-lg border border-[rgba(0,255,157,0.08)] bg-[rgba(0,255,157,0.02)] p-2.5 text-[9px] font-mono flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-[#00FF9D] rounded-full animate-pulse" />
                    COMM_LINK: CONNECTED
                </span>
                <span>AETHER OS v2.4.1</span>
            </div>
        </div>
    );
}
