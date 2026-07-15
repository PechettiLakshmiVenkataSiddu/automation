'use client';

import { ChangeEvent, RefObject } from 'react';
import { GlassPanel } from './GlassPanel';

type VoiceControlsProps = {
    busy: boolean;
    captureEnabled: boolean;
    retentionEnabled: boolean;
    sessionId: string | null;
    toggleConsent: (enabled: boolean) => void;
    setRetentionEnabled: (enabled: boolean) => void;
    startSession: () => void;
    fileInputRef: RefObject<HTMLInputElement | null>;
    uploadAudio: (file: File) => void;
};

export function VoiceControls({
    busy,
    captureEnabled,
    retentionEnabled,
    sessionId,
    toggleConsent,
    setRetentionEnabled,
    startSession,
    fileInputRef,
    uploadAudio,
}: VoiceControlsProps) {

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) void uploadAudio(file);
    };

    return (
        <div className="space-y-6 flex flex-col h-full">
            {/* Settings & Consent Panel */}
            <GlassPanel glowColor="rgba(0, 255, 157, 0.08)">
                <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#00FF9D] border-b border-[rgba(0,255,157,0.12)] pb-3 mb-4.5 font-mono">
                    SETTINGS & CONSENT
                </h3>

                <div className="flex flex-col gap-3">
                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => toggleConsent(true)}
                        className={`w-full rounded-xl border py-3.5 px-5 text-xs font-bold tracking-widest uppercase transition-all duration-300 flex items-center justify-between cursor-pointer focus:outline-none ${captureEnabled
                                ? 'bg-[rgba(0,255,157,0.06)] border-[#00FF9D] text-[#00FF9D] shadow-[0_0_12px_rgba(0,255,157,0.15)]'
                                : 'bg-transparent border-[rgba(255,255,255,0.06)] text-slate-400 hover:border-[#00FF9D] hover:text-[#00FF9D]'
                            }`}
                    >
                        <span>ENABLE CONSENT</span>
                        <span className={`w-2.5 h-2.5 rounded-full ${captureEnabled ? 'bg-[#00FF9D] shadow-[0_0_8px_#00FF9D]' : 'bg-slate-750'}`} />
                    </button>

                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => toggleConsent(false)}
                        className="w-full rounded-xl border border-[rgba(255,82,82,0.15)] bg-transparent hover:bg-[rgba(255,82,82,0.05)] hover:border-[#FF5252] py-3.5 px-5 text-xs font-bold tracking-widest uppercase text-[#FF5252] transition-all duration-300 flex items-center justify-between cursor-pointer focus:outline-none"
                    >
                        <span>WITHDRAW CONSENT</span>
                        <span className="w-2.5 h-2.5 rounded-full bg-[#FF5252] shadow-[0_0_8px_#FF5252]" />
                    </button>
                </div>

                <label className="flex items-center gap-3 text-[10px] text-slate-400 cursor-pointer select-none py-3 mt-2 hover:text-white transition-colors duration-200">
                    <input
                        type="checkbox"
                        checked={retentionEnabled}
                        disabled={!captureEnabled || busy}
                        className="rounded border-[rgba(0,255,157,0.25)] bg-slate-950 text-[#00FF9D] focus:ring-opacity-20 focus:ring-[#00FF9D] w-4 h-4 cursor-pointer"
                        onChange={(event) => setRetentionEnabled(event.target.checked)}
                    />
                    <span className="font-mono uppercase tracking-widest">Retain voice recordings block</span>
                </label>
            </GlassPanel>

            {/* Session Controls Panel */}
            <GlassPanel glowColor="rgba(0, 217, 255, 0.08)">
                <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#00D9FF] border-b border-[rgba(0,217,255,0.12)] pb-3 mb-4.5 font-mono">
                    SESSION MODULES
                </h3>

                <div className="space-y-4">
                    <button
                        type="button"
                        disabled={busy || !captureEnabled}
                        onClick={startSession}
                        className={`w-full rounded-xl border py-4 px-5 text-xs font-bold tracking-widest uppercase transition-all duration-300 flex items-center justify-between cursor-pointer focus:outline-none ${sessionId
                                ? 'bg-[rgba(0,217,255,0.06)] border-[#00D9FF] text-[#00D9FF] shadow-[0_0_12px_rgba(0,217,255,0.15)]'
                                : 'bg-slate-900 border-[rgba(255,255,255,0.06)] text-slate-300 hover:border-[#00D9FF] hover:text-[#00D9FF] disabled:opacity-40 disabled:pointer-events-none'
                            }`}
                    >
                        <span>{sessionId ? 'SESSION ACTIVE' : 'START NEW SESSION'}</span>
                        {sessionId ? (
                            <span className="flex h-2.5 w-2.5 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00D9FF] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#00D9FF]"></span>
                            </span>
                        ) : (
                            <svg className="w-4.5 h-4.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            </svg>
                        )}
                    </button>

                    <button
                        type="button"
                        disabled={busy || !sessionId}
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full rounded-xl border border-[rgba(255,255,255,0.06)] bg-transparent hover:border-[#79FFE8] hover:text-[#79FFE8] py-4 px-5 text-xs font-bold tracking-widest uppercase text-slate-400 transition-all duration-300 flex items-center justify-between cursor-pointer focus:outline-none disabled:opacity-30 disabled:pointer-events-none"
                    >
                        <span>UPLOAD AUDIO FILE</span>
                        <svg className="w-4.5 h-4.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="audio/*"
                        className="hidden"
                        onChange={handleFileChange}
                    />
                </div>
            </GlassPanel>
        </div>
    );
}
