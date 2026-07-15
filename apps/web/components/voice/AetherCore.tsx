'use client';

import { GlassPanel } from './GlassPanel';
import { VoiceOrb } from './VoiceOrb';

type AetherCoreProps = {
    stream: MediaStream | null;
    isRecording: boolean;
    isThinking: boolean;
    isSpeaking: boolean;
    onClick: () => void;
    disabled: boolean;
};

export function AetherCore({
    stream,
    isRecording,
    isThinking,
    isSpeaking,
    onClick,
    disabled,
}: AetherCoreProps) {
    return (
        <GlassPanel
            glowColor={isRecording ? 'rgba(0, 255, 157, 0.12)' : isThinking ? 'rgba(0, 217, 255, 0.12)' : 'rgba(0, 255, 157, 0.05)'}
            className="flex-1 flex flex-col justify-between min-h-[600px] h-full"
        >
            {/* HUD Panel Header */}
            <div className="flex justify-between items-center border-b border-[rgba(0,255,157,0.12)] pb-3.5 mb-4">
                <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#00FF9D] font-mono">
                    AETHER QUANTUM CORE
                </h3>
                <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${isRecording ? 'bg-red-500 animate-ping' : isThinking ? 'bg-[#00D9FF] animate-pulse' : 'bg-blue-500'}`} />
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono tracking-widest">
                        {isRecording ? 'CAPTURING_MIC' : isThinking ? 'COGNITIVE_PARSE' : 'CORE_STANDBY'}
                    </span>
                </div>
            </div>

            {/* Central Visualizer Orb Element */}
            <div className="flex-1 flex items-center justify-center py-4">
                <VoiceOrb
                    stream={stream}
                    isRecording={isRecording}
                    isThinking={isThinking}
                    isSpeaking={isSpeaking}
                    onClick={onClick}
                    disabled={disabled}
                />
            </div>

            {/* Dynamic Command Assist Bar */}
            <div className="mt-4 w-full bg-[rgba(5,7,10,0.55)] p-4 rounded-xl border border-[rgba(0,255,157,0.06)] text-center flex items-center justify-center min-h-[60px] font-mono shadow-inner">
                {isRecording ? (
                    <p className="text-xs text-[#88FFCC] tracking-widest uppercase animate-pulse">
                        &gt;&gt; SYSTEM DIRECTIVE: LISTENING ON DEBIT COMM INTR...
                    </p>
                ) : isThinking ? (
                    <p className="text-xs text-[#00D9FF] tracking-widest uppercase animate-pulse">
                        &gt;&gt; COGNITIVE SYNERGY: RUNNING PIPELINE PARSE...
                    </p>
                ) : (
                    <p className="text-[10px] text-slate-450 tracking-widest uppercase">
                        {disabled
                            ? 'ESTABLISH ACTIVE LIFE SESSION SESSION LINK TO REKey CORE'
                            : 'PRESS TRANSCENDENT CORE SPHERE TO KEY INTERNET TRANSMITTER'}
                    </p>
                )}
            </div>
        </GlassPanel>
    );
}
