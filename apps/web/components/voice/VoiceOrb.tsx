'use client';

import { useEffect, useRef, useState } from 'react';

type VoiceOrbProps = {
    stream: MediaStream | null;
    isRecording: boolean;
    isThinking: boolean;
    isSpeaking: boolean;
    onClick?: () => void;
    disabled?: boolean;
};

function getRgba(hexOrRgba: string, opacity: number): string {
    if (hexOrRgba.startsWith('#')) {
        const r = parseInt(hexOrRgba.slice(1, 3), 16);
        const g = parseInt(hexOrRgba.slice(3, 5), 16);
        const b = parseInt(hexOrRgba.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    if (hexOrRgba.startsWith('rgba')) {
        return hexOrRgba.replace(/,?\s*[\d.]+\s*\)$/, `, ${opacity})`);
    }
    return hexOrRgba;
}

export function VoiceOrb({
    stream,
    isRecording,
    isThinking,
    isSpeaking,
    onClick,
    disabled = false,
}: VoiceOrbProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationFrameRef = useRef<number | null>(null);

    // Standby breathing phase
    const breathingPhaseRef = useRef(0);

    // UI Hover ring pulse
    const [isHovered, setIsHovered] = useState(false);

    // Setup Web Audio API
    useEffect(() => {
        if (!stream) {
            // Disconnect if stream goes null
            cleanupAudio();
            return;
        }

        try {
            const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
            const ctx = new AudioCtx();
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;

            const source = ctx.createMediaStreamSource(stream);
            source.connect(analyser);

            audioCtxRef.current = ctx;
            analyserRef.current = analyser;
            sourceRef.current = source;
        } catch (e) {
            console.error('Failed to initialize voice analyzer:', e);
        }

        return () => cleanupAudio();
    }, [stream]);

    const cleanupAudio = () => {
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
        }
        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
            void audioCtxRef.current.close();
            audioCtxRef.current = null;
        }
        analyserRef.current = null;
    };

    // Canvas drawing loop
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let particleAngle = 0;
        const dataArray = new Uint8Array(128);

        const draw = () => {
            // Hardware resize adjustment
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
                canvas.width = rect.width * dpr;
                canvas.height = rect.height * dpr;
            }
            ctx.scale(dpr, dpr);

            const width = rect.width;
            const height = rect.height;
            const centerX = width / 2;
            const centerY = height / 2;

            ctx.clearRect(0, 0, width, height);

            // Get amplitude frequencies
            let amplitudeSum = 0;
            if (analyserRef.current && isRecording) {
                analyserRef.current.getByteFrequencyData(dataArray);
                amplitudeSum = dataArray.reduce((acc, v) => acc + v, 0) / 128;
            }

            // Standby breathing offset calculator
            breathingPhaseRef.current += isThinking ? 0.08 : 0.02;
            const breath = Math.sin(breathingPhaseRef.current) * 0.08;

            // Calculate dynamics mapping
            const baseRadius = 88 + (isHovered ? 6 : 0) + breath * 30;
            const amplitudeModifier = isRecording ? (amplitudeSum / 255) * 80 : 0;
            const dynamicRadius = baseRadius + amplitudeModifier;

            // Color Theme Selection Mapping
            let primaryColor = '#00FF9D'; // default neon green
            let secondaryColor = '#00D9FF'; // default cyan

            if (isThinking) {
                primaryColor = '#00D9FF'; // blue rotating theme
                secondaryColor = '#79FFE8';
            } else if (isSpeaking) {
                primaryColor = '#79FFE8'; // processing glow mint
                secondaryColor = '#00FF9D';
            } else if (!isRecording) {
                primaryColor = 'rgba(0, 255, 157, 0.45)'; // muted standby green
                secondaryColor = 'rgba(0, 217, 255, 0.15)';
            }

            // Render Layer 1: Ambient Backdrop Pulse Blur Glow
            const glowGrad = ctx.createRadialGradient(centerX, centerY, dynamicRadius * 0.4, centerX, centerY, dynamicRadius * 1.8);
            glowGrad.addColorStop(0, getRgba(primaryColor, 0.08));
            glowGrad.addColorStop(0.5, getRgba(secondaryColor, 0.03));
            glowGrad.addColorStop(1, 'transparent');
            ctx.fillStyle = glowGrad;
            ctx.beginPath();
            ctx.arc(centerX, centerY, dynamicRadius * 1.8, 0, Math.PI * 2);
            ctx.fill();

            // Render Layer 2: Main Concentric Rotating Mechanised Core Ring
            ctx.strokeStyle = primaryColor;
            ctx.lineWidth = isRecording ? 3.5 : 2;
            ctx.shadowBlur = 15;
            ctx.shadowColor = primaryColor;
            ctx.beginPath();
            ctx.arc(centerX, centerY, dynamicRadius, 0, Math.PI * 2);
            ctx.stroke();
            ctx.shadowBlur = 0; // reset shadow index

            // Render Layer 3: Circular Frequency Spectrum Arc Spikes (when active)
            if (isRecording && analyserRef.current) {
                const spikeCount = 80;
                ctx.strokeStyle = secondaryColor;
                ctx.lineWidth = 2.5;

                for (let i = 0; i < spikeCount; i += 2) {
                    const freqVal = dataArray[i % dataArray.length] || 0;
                    const arcAngle = (i / spikeCount) * Math.PI * 2 + breathingPhaseRef.current * 0.1;
                    const spikeLength = (freqVal / 255) * 60;

                    const startX = centerX + Math.cos(arcAngle) * dynamicRadius;
                    const startY = centerY + Math.sin(arcAngle) * dynamicRadius;
                    const endX = centerX + Math.cos(arcAngle) * (dynamicRadius + spikeLength);
                    const endY = centerY + Math.sin(arcAngle) * (dynamicRadius + spikeLength);

                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(endX, endY);
                    ctx.stroke();
                }
            }

            // Render Layer 4: Concentric Mechanical Rotating HUD Rings
            ctx.strokeStyle = getRgba(secondaryColor, 0.25);
            ctx.lineWidth = 1;

            // Ring A: Rotating Dash Ring
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(breathingPhaseRef.current * (isThinking ? 0.8 : 0.2));
            ctx.setLineDash([8, 12]);
            ctx.beginPath();
            ctx.arc(0, 0, dynamicRadius + 22, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();

            // Ring B: Orbiting Mechanical Markers
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(-breathingPhaseRef.current * 0.15);
            ctx.setLineDash([40, 140]);
            ctx.strokeStyle = getRgba(primaryColor, 0.2);
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(0, 0, dynamicRadius + 38, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();

            // Render Layer 5: Floating Orbiting Particles (Jarvis Neural Style)
            particleAngle += 0.01 + (amplitudeModifier * 0.002);
            const particleRadius = dynamicRadius - 20;
            ctx.fillStyle = primaryColor;

            for (let i = 0; i < 4; i++) {
                const offsetAngle = (i * Math.PI) / 2 + particleAngle;
                const px = centerX + Math.cos(offsetAngle) * (particleRadius + Math.sin(breathingPhaseRef.current * 2 + i) * 6);
                const py = centerY + Math.sin(offsetAngle) * (particleRadius + Math.sin(breathingPhaseRef.current * 2 + i) * 6);

                ctx.shadowBlur = 8;
                ctx.shadowColor = primaryColor;
                ctx.beginPath();
                ctx.arc(px, py, 2.5, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;
            }

            animationFrameRef.current = requestAnimationFrame(draw);
        };

        draw();

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [isRecording, isThinking, isSpeaking, isHovered]);

    return (
        <div className="flex flex-col items-center justify-center p-6 relative">
            <div
                className="w-[360px] h-[360px] relative flex items-center justify-center cursor-pointer select-none rounded-full"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onClick={() => !disabled && onClick?.()}
            >
                <canvas
                    ref={canvasRef}
                    className="absolute inset-0 w-full h-full"
                />

                {/* Center UI Inner Sphere Element */}
                <div
                    className={`w-32 h-32 rounded-full flex flex-col items-center justify-center relative transition-all duration-500 shadow-xl border ${isThinking
                        ? 'border-[#00D9FF] bg-[rgba(0,217,255,0.06)] shadow-[0_0_24px_rgba(0,217,255,0.15)]'
                        : isRecording
                            ? 'border-[#00FF9D] bg-[rgba(0,255,157,0.08)] shadow-[0_0_28px_rgba(0,255,157,0.25)] scale-105'
                            : 'border-[rgba(255,255,255,0.08)] bg-slate-950/70 hover:border-[#00FF9D]/40'
                        }`}
                >
                    {isThinking ? (
                        <div className="flex flex-col items-center justify-center gap-1.5 animate-pulse text-[#00D9FF]">
                            <span className="text-[10px] font-bold tracking-widest font-mono">THINKING</span>
                            <span className="text-[8px] font-mono text-slate-500">AETH_V3_COGNITIVE</span>
                        </div>
                    ) : isRecording ? (
                        <div className="flex flex-col items-center justify-center gap-1.5 text-[#00FF9D]">
                            <span className="text-[10px] font-mono font-bold tracking-widest animate-pulse">LISTENING</span>
                            <span className="text-[8px] font-mono text-slate-450 tracking-wider">CLICK_TO_STOP</span>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center gap-1.5 text-slate-400 hover:text-white transition-colors duration-300">
                            <svg className="w-9 h-9" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                            <span className="text-[9px] font-mono font-black tracking-widest uppercase">
                                {disabled ? 'LOCKED' : 'CLICK TO KEY'}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
