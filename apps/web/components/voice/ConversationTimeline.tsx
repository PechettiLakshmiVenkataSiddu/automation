'use client';

import { useEffect, useRef } from 'react';
import { GlassPanel } from './GlassPanel';

export type TimelineMessage = {
    id: string;
    role: 'user' | 'assistant';
    text: string;
    isSpeaking?: boolean;
};

type TimelineProps = {
    messages: TimelineMessage[];
    isMuted: boolean;
    setIsMuted: (value: boolean) => void;
    isSpeaking: boolean;
    onStopSpeaking: () => void;
    onReplay: (text: string) => void;
};

export function ConversationTimeline({
    messages,
    isMuted,
    setIsMuted,
    isSpeaking,
    onStopSpeaking,
    onReplay,
}: TimelineProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Keep timeline scrolled to bottom
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <GlassPanel glowColor="rgba(0, 217, 255, 0.04)" className="min-h-[420px] flex flex-col h-full">
            {/* Timeline Controls Header */}
            <div className="flex justify-between items-center border-b border-[rgba(0,255,157,0.12)] pb-4 mb-4.5">
                <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#00FF9D] font-mono flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-[#00FF9D] rounded-full animate-pulse" />
                    ACTIVE DIALOG TIMELINE
                </h3>

                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => setIsMuted(!isMuted)}
                        className={`cursor-pointer px-3.5 py-1.5 rounded-lg border text-[10px] font-mono uppercase tracking-widest font-black transition-all ${isMuted
                                ? 'border-[#FF5252] bg-[rgba(255,82,82,0.06)] text-[#FF5252]'
                                : 'border-[rgba(0,255,157,0.25)] bg-[rgba(0,255,157,0.02)] text-[#00FF9D] hover:border-[#00FF9D]'
                            }`}
                    >
                        {isMuted ? 'Muted' : 'Voice Output'}
                    </button>

                    <button
                        type="button"
                        disabled={!isSpeaking}
                        onClick={onStopSpeaking}
                        className="cursor-pointer px-3.5 py-1.5 rounded-lg border border-[rgba(255,255,255,0.06)] hover:border-[#FF5252] hover:text-[#FF5252] bg-transparent text-slate-400 text-[10px] font-mono uppercase tracking-widest transition-all disabled:opacity-30 disabled:pointer-events-none"
                    >
                        Stop Speech
                    </button>
                </div>
            </div>

            {/* Log Feed */}
            <div
                ref={containerRef}
                className="flex-1 overflow-y-auto pr-1 space-y-4 max-h-[300px] scrollbar-thin scrollbar-thumb-slate-900 scrollbar-track-transparent"
            >
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-slate-500 font-mono text-center text-xs p-6 select-none leading-relaxed">
                        [AETHER CORE DETECTED]<br />
                        NO DIALOG TRANSMISSION RECORDED FOR ACTIVE LIFELINE
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex w-full ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}
                        >
                            <div
                                className={`max-w-[85%] rounded-xl p-4 border font-mono text-xs relative space-y-1 ${msg.role === 'user'
                                        ? 'bg-slate-950 border-[rgba(255,255,255,0.06)] text-[#88FFCC]'
                                        : 'bg-[rgba(11,17,24,0.65)] border-[rgba(0,255,157,0.15)] text-slate-100'
                                    }`}
                            >
                                <div className="flex justify-between items-center text-[8px] text-slate-500 uppercase tracking-widest font-black mb-1 select-none">
                                    <span>{msg.role === 'user' ? 'User Stream' : 'Aether Resp'}</span>
                                    {msg.role === 'assistant' && (
                                        <button
                                            type="button"
                                            onClick={() => onReplay(msg.text)}
                                            className="text-[#00D9FF] hover:underline cursor-pointer tracking-wider"
                                        >
                                            [REPLAY]
                                        </button>
                                    )}
                                </div>

                                <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>

                                {msg.isSpeaking && (
                                    <div className="flex items-center gap-1 mt-2.5 pt-1.5 border-t border-[rgba(0,255,157,0.08)] text-[#00FF9D] text-[9px] uppercase font-bold tracking-widest animate-pulse">
                                        <span className="flex h-1.5 w-1.5 relative">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00FF9D] opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#00FF9D]"></span>
                                        </span>
                                        VOICE_SPEAKING_ALOUD
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </GlassPanel>
    );
}
