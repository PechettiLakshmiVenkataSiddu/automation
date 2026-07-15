'use client';

import { ChangeEvent, RefObject } from 'react';

type CommandCenterProps = {
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

export function VoiceCommandCenter({
    busy,
    captureEnabled,
    retentionEnabled,
    sessionId,
    toggleConsent,
    setRetentionEnabled,
    startSession,
    fileInputRef,
    uploadAudio,
}: CommandCenterProps) {

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) void uploadAudio(file);
    };

    return (
        <aside className="space-y-6">
            {/* Settings & Consent Panel */}
            <section className="rounded-xl border border-[rgba(0,255,157,0.18)] bg-[rgba(5,7,10,0.65)] backdrop-blur-md p-5 shadow-lg relative overflow-hidden space-y-4">
                <div className="absolute top-0 left-0 w-16 h-[2px] bg-gradient-to-r from-[#00FF9D] to-transparent" />
                <div className="absolute top-0 left-0 w-[2px] h-16 bg-gradient-to-b from-[#00FF9D] to-transparent" />

                <h3 className="text-xs uppercase font-extrabold tracking-[0.2em] text-[#00FF9D] border-b border-[rgba(0,255,157,0.1)] pb-2">
                    SETTINGS & CONSENT
                </h3>

                <div className="flex flex-col gap-2.5">
                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => toggleConsent(true)}
                        className={`w-full rounded-lg border py-3 px-4 text-xs font-bold tracking-wider uppercase transition-all duration-300 flex items-center justify-between cursor-pointer ${captureEnabled
                                ? 'bg-[rgba(0,255,157,0.06)] border-[#00FF9D] text-[#00FF9D] shadow-[0_0_12px_rgba(0,255,157,0.15)]'
                                : 'bg-transparent border-[rgba(255,255,255,0.08)] text-slate-400 hover:border-[#00FF9D] hover:text-[#00FF9D]'
                            }`}
                    >
                        <span>ENABLE CONSENT</span>
                        <span className={`w-2 h-2 rounded-full ${captureEnabled ? 'bg-[#00FF9D] shadow-[0_0_6px_#00FF9D]' : 'bg-slate-700'}`} />
                    </button>

                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => toggleConsent(false)}
                        className="w-full rounded-lg border border-[rgba(255,77,77,0.2)] bg-transparent hover:bg-[rgba(255,77,77,0.05)] hover:border-[#FF4D4D] py-3 px-4 text-xs font-bold tracking-wider uppercase text-[#FF4D4D] transition-all duration-300 flex items-center justify-between cursor-pointer"
                    >
                        <span>WITHDRAW CONSENT</span>
                        <span className="w-2 h-2 rounded-full bg-[#FF4D4D] shadow-[0_0_6px_#FF4D4D]" />
                    </button>
                </div>

                <label className="flex items-center gap-2.5 text-[10px] text-slate-400 cursor-pointer select-none py-1 hover:text-white transition-colors duration-200">
                    <input
                        type="checkbox"
                        checked={retentionEnabled}
                        disabled={!captureEnabled || busy}
                        className="rounded border-[rgba(0,255,157,0.3)] bg-slate-950 text-[#00FF9D] focus:ring-opacity-20 focus:ring-[#00FF9D] w-3.5 h-3.5"
                        onChange={(event) => setRetentionEnabled(event.target.checked)}
                    />
                    <span className="font-mono uppercase tracking-wider">Retain voice recordings block</span>
                </label>
            </section>

            {/* Session Controls Panel */}
            <section className="rounded-xl border border-[rgba(0,255,157,0.18)] bg-[rgba(5,7,10,0.65)] backdrop-blur-md p-5 shadow-lg relative overflow-hidden space-y-4">
                <div className="absolute top-0 left-0 w-16 h-[2px] bg-gradient-to-r from-[#00E5FF] to-transparent" />
                <div className="absolute top-0 left-0 w-[2px] h-16 bg-gradient-to-b from-[#00E5FF] to-transparent" />

                <h3 className="text-xs uppercase font-extrabold tracking-[0.2em] text-[#00E5FF] border-b border-[rgba(0,229,255,0.1)] pb-2">
                    SESSION
                </h3>

                <div className="space-y-3">
                    <button
                        type="button"
                        disabled={busy || !captureEnabled}
                        onClick={startSession}
                        className={`w-full rounded-lg border py-3 px-4 text-xs font-bold tracking-wider uppercase transition-all duration-300 flex items-center justify-between cursor-pointer ${sessionId
                                ? 'bg-[rgba(0,229,255,0.06)] border-[#00E5FF] text-[#00E5FF] shadow-[0_0_12px_rgba(0,229,255,0.15)]'
                                : 'bg-slate-900 border-[rgba(255,255,255,0.08)] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF] disabled:opacity-40 disabled:pointer-events-none'
                            }`}
                    >
                        <span>{sessionId ? 'SESSION ACTIVE' : 'START NEW SESSION'}</span>
                        {sessionId ? (
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00E5FF] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00E5FF]"></span>
                            </span>
                        ) : (
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            </svg>
                        )}
                    </button>

                    <button
                        type="button"
                        disabled={busy || !sessionId}
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full rounded-lg border border-[rgba(255,255,255,0.08)] bg-transparent hover:border-[#88FFCC] hover:text-[#88FFCC] py-3 px-4 text-xs font-bold tracking-wider uppercase text-slate-350 transition-all duration-300 flex items-center justify-between cursor-pointer disabled:opacity-30 disabled:pointer-events-none"
                    >
                        <span>UPLOAD AUDIO CLIP</span>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            </section>
        </aside>
    );
}
