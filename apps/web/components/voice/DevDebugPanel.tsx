'use client';

import { GlassPanel } from './GlassPanel';

type DevDebugProps = {
    permission: string;
    isRecording: boolean;
    blobSize: number; // in bytes
    recordingTime: number; // in seconds
    transcriptStatus: string;
    chatRequestStatus: string;
    speechStatus: string;
    conversationId: string | null;
    sessionId: string | null;
    latency: number; // in ms
    lastError: string | null;
};

export function DevDebugPanel({
    permission,
    isRecording,
    blobSize,
    recordingTime,
    transcriptStatus,
    chatRequestStatus,
    speechStatus,
    conversationId,
    sessionId,
    latency,
    lastError,
}: DevDebugProps) {
    // Only render during development environment
    if (process.env.NODE_ENV !== 'development') {
        return null;
    }

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 KB';
        return `${(bytes / 1024).toFixed(2)} KB`;
    };

    return (
        <GlassPanel glowColor="rgba(255, 82, 82, 0.08)" className="mt-6 flex flex-col font-mono text-[9px] text-slate-350">
            <h3 className="text-xs uppercase font-extrabold tracking-[0.25em] text-[#FF5252] border-b border-[rgba(255,82,82,0.15)] pb-3 mb-4.5 font-mono">
                DEV DIAGNOSTIC CORE
            </h3>

            <div className="space-y-2 flex-1">
                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Permission:</span>
                    <span className={permission === 'granted' ? 'text-[#00FF9D]' : 'text-[#FF5252]'}>{permission.toUpperCase()}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Recording:</span>
                    <span>{isRecording ? 'ACTIVE' : 'IDLE'}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Blob Size:</span>
                    <span>{formatSize(blobSize)}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Duration:</span>
                    <span>{recordingTime.toFixed(1)}s</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black font-mono">Transcription:</span>
                    <span className="text-[#00D9FF]">{transcriptStatus.toUpperCase()}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Chat Request:</span>
                    <span className="truncate max-w-[140px]">{chatRequestStatus.toUpperCase()}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Speech Status:</span>
                    <span>{speechStatus.toUpperCase()}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Conversation ID:</span>
                    <span className="truncate max-w-[140px]">{conversationId || 'N/A'}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Session ID:</span>
                    <span className="truncate max-w-[140px]">{sessionId || 'N/A'}</span>
                </div>

                <div className="flex justify-between border-b border-[rgba(255,255,255,0.03)] pb-1">
                    <span className="text-slate-500 uppercase font-black">Poll Latency:</span>
                    <span>{latency > 0 ? `${latency}ms` : 'N/A'}</span>
                </div>

                {lastError && (
                    <div className="rounded-lg bg-[rgba(255,82,82,0.05)] border border-[rgba(255,82,82,0.15)] p-3 text-[#FF5252] break-words uppercase font-bold text-[8px] leading-relaxed">
                        CRITICAL_ERR: {lastError}
                    </div>
                )}
            </div>
        </GlassPanel>
    );
}
