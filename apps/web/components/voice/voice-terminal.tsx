'use client';

import { FormEvent } from 'react';

type PendingConfirmation = {
    confirmation_id: string;
    intent_type: string;
    transcript: string;
    payload?: any;
};

type TerminalProps = {
    transcript: string;
    setTranscript: (text: string) => void;
    busy: boolean;
    sessionId: string | null;
    submitTranscript: (event?: FormEvent<HTMLFormElement>) => void;
    pending: PendingConfirmation | null;
    decide: (confirmed: boolean) => void;
    status: string | null;
    error: string | null;
};

export function VoiceTerminal({
    transcript,
    setTranscript,
    busy,
    sessionId,
    submitTranscript,
    pending,
    decide,
    status,
    error,
}: TerminalProps) {

    const handleFormSubmit = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        submitTranscript(e);
    };

    return (
        <div className="space-y-6">
            {/* Interactive Monospace Command Terminal */}
            <form onSubmit={handleFormSubmit} className="rounded-xl border border-[rgba(0,255,157,0.18)] bg-[rgba(5,7,10,0.85)] p-5 shadow-2xl relative overflow-hidden space-y-4">
                <div className="absolute top-0 left-0 w-16 h-[2px] bg-gradient-to-r from-[#00FF9D] to-transparent" />
                <div className="absolute top-0 left-0 w-[2px] h-16 bg-gradient-to-b from-[#00FF9D] to-transparent" />

                <div className="flex justify-between items-center border-b border-[rgba(0,255,157,0.1)] pb-2">
                    <span className="text-xs uppercase font-extrabold tracking-[0.2em] text-[#00FF9D] flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 bg-[#00FF9D] rounded-full animate-ping" />
                        AETHER CONSOLE TERMINAL
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">ASCII LOGS: ACTIVE</span>
                </div>

                <div className="relative">
                    <textarea
                        id="voice-transcript"
                        value={transcript}
                        onChange={(event) => setTranscript(event.target.value)}
                        rows={4}
                        className="w-full rounded-lg border border-[rgba(0,255,157,0.1)] focus:border-[#00FF9D] bg-slate-950 px-4 py-3.5 text-xs font-mono text-[#88FFCC] placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-[#00FF9D] resize-none tracking-wide"
                        placeholder="Record your voice command above, or type an instruction here..."
                    />
                    <div className="absolute right-3.5 bottom-3.5 text-[9px] font-mono text-slate-500">
                        {transcript.length} / 4000
                    </div>
                </div>

                <div className="flex justify-between items-center">
                    <button
                        type="submit"
                        disabled={busy || !sessionId || !transcript.trim()}
                        className="rounded-lg bg-transparent border border-[#00FF9D] hover:bg-[rgba(0,255,157,0.06)] disabled:opacity-30 disabled:border-slate-800 disabled:text-slate-650 px-6 py-2.5 text-xs font-mono font-bold tracking-wider uppercase text-[#00FF9D] transition-all duration-300 shadow-[0_0_12px_rgba(0,255,157,0.08)] cursor-pointer"
                    >
                        {busy ? 'PARSING ENGINE...' : 'PARSE COMMAND'}
                    </button>
                    <span className="text-[9px] font-mono text-slate-500">ROOT@AETHER_AGENT_SYS</span>
                </div>
            </form>

            {/* Status Logs and Errors Display */}
            {status && (
                <div className="rounded-lg border border-[#00FF9D] bg-[rgba(0,255,157,0.02)] p-3.5 text-xs font-mono text-[#00FF9D] flex items-center justify-between shadow-[0_0_8px_rgba(0,255,157,0.05)]">
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-[#00FF9D] rounded-full animate-ping" />
                        <span>[SYS_LOG]: {status}</span>
                    </div>
                </div>
            )}

            {error && (
                <div className="rounded-lg border border-[#FF4D4D] bg-[rgba(255,77,77,0.02)] p-3.5 text-xs font-mono text-[#FF4D4D] flex items-center justify-between shadow-[0_0_8px_rgba(255,77,77,0.05)] animate-shake">
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-[#FF4D4D] rounded-full animate-pulse" />
                        <span>[ERR_LOG]: {error}</span>
                    </div>
                </div>
            )}

            {/* Live Action Preview Panel */}
            {pending && (
                <article className="rounded-xl border border-[rgba(0,229,255,0.18)] bg-[rgba(5,7,10,0.65)] p-5 shadow-lg relative overflow-hidden space-y-4">
                    <div className="absolute top-0 left-0 w-16 h-[2px] bg-gradient-to-r from-[#00E5FF] to-transparent" />

                    <div className="flex justify-between items-center border-b border-[rgba(0,229,255,0.1)] pb-2">
                        <span className="text-xs uppercase font-extrabold tracking-[0.2em] text-[#00E5FF]">
                            INTENT PREVIEW PAYLOAD
                        </span>
                        <span className="px-2 py-0.5 rounded border border-[#00E5FF] bg-[rgba(0,229,255,0.05)] text-[9px] font-mono font-extrabold text-[#00E5FF]">
                            {pending.intent_type}
                        </span>
                    </div>

                    <div className="space-y-3 font-mono text-xs">
                        <div>
                            <p className="text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1">TRANSCRIPT</p>
                            <p className="text-xs font-semibold text-[#88FFCC] italic">&quot;{pending.transcript}&quot;</p>
                        </div>
                        {pending.payload && (
                            <div>
                                <p className="text-[9px] uppercase font-bold text-slate-400 tracking-wider mb-1">ARGS PAYLOAD</p>
                                <pre className="text-[10px] bg-slate-950 p-3 rounded-lg border border-[rgba(255,255,255,0.03)] text-slate-300 overflow-auto max-h-32 leading-relaxed">
                                    {JSON.stringify(pending.payload, null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                </article>
            )}

            {/* Confirmation Modal */}
            {pending && (
                <div className="fixed inset-0 overflow-y-auto z-50 flex items-center justify-center p-4 bg-[rgba(3,5,8,0.75)] backdrop-blur-md">
                    <div className="bg-slate-950 rounded-2xl max-w-sm w-full border border-[rgba(0,255,157,0.18)] shadow-2xl p-6 relative flex flex-col space-y-5">
                        <div className="absolute top-0 left-0 w-24 h-[2px] bg-gradient-to-r from-[#00FF9D] to-transparent" />

                        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-[rgba(255,217,61,0.08)] border border-[#FFD93D] text-[#FFD93D] shadow-[0_0_12px_rgba(255,217,61,0.15)]">
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>

                        <div className="text-center space-y-1">
                            <h3 className="text-sm uppercase font-black font-mono tracking-wider text-white">CONFIRM INTENT</h3>
                            <p className="text-[10px] text-slate-400 leading-normal">
                                Verify execution parameters before committing this voice action.
                            </p>
                        </div>

                        <div className="bg-slate-900 border border-[rgba(0,255,157,0.06)] p-3.5 rounded-lg text-left space-y-2">
                            <div className="flex justify-between items-center text-[8px] text-[#00FF9D] uppercase font-black font-mono">
                                <span>INTENT: {pending.intent_type}</span>
                            </div>
                            <p className="text-xs font-semibold text-slate-200 font-mono">
                                &quot;{pending.transcript}&quot;
                            </p>
                        </div>

                        <div className="flex flex-col gap-2">
                            <button
                                type="button"
                                disabled={busy}
                                onClick={() => decide(true)}
                                className="w-full rounded-lg bg-[rgba(0,255,157,0.06)] border border-[#00FF9D] py-3 text-xs font-bold font-mono tracking-widest text-[#00FF9D] shadow-lg hover:bg-[rgba(0,255,157,0.12)] transition-all cursor-pointer"
                            >
                                EXECUTE ACTION
                            </button>
                            <button
                                type="button"
                                disabled={busy}
                                onClick={() => decide(false)}
                                className="w-full rounded-lg border border-[rgba(255,255,255,0.08)] bg-transparent py-3 text-xs font-bold font-mono tracking-widest text-slate-400 hover:text-white hover:border-slate-500 transition-all cursor-pointer"
                            >
                                CANCEL SUBMISSION
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
