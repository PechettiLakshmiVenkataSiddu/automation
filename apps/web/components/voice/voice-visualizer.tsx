'use client';

import { useEffect, useRef, useState } from 'react';

type VoiceVisualizerProps = {
    stream: MediaStream | null;
    isRecording: boolean;
    onClick?: () => void;
    disabled?: boolean;
};

type Particle = {
    angle: number;
    baseRadius: number;
    radius: number;
    speed: number;
    size: number;
    color: string;
};

export function VoiceVisualizer({ stream, isRecording, onClick, disabled }: VoiceVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

    // Animation state references
    const rotationAngleRef = useRef(0);
    const outerRotationRef = useRef(0);
    const particlesRef = useRef<Particle[]>([]);
    const animationFrameIdRef = useRef<number | null>(null);

    // Initialize orbiting particles once
    if (particlesRef.current.length === 0) {
        const temp: Particle[] = [];
        for (let i = 0; i < 20; i++) {
            temp.push({
                angle: Math.random() * Math.PI * 2,
                baseRadius: 110 + Math.random() * 40,
                radius: 0,
                speed: (Math.random() * 0.01 + 0.005) * (Math.random() < 0.5 ? 1 : -1),
                size: Math.random() * 2 + 1,
                color: Math.random() < 0.6 ? '#00FF9D' : '#00E5FF',
            });
        }
        particlesRef.current = temp;
    }

    useEffect(() => {
        if (!stream) {
            // Clean up Web Audio API nodes if stream is closed
            cleanupAudioNodes();
            return;
        }

        try {
            const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
            const audioContext = new AudioCtx();
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.8;

            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);

            audioContextRef.current = audioContext;
            analyserRef.current = analyser;
            sourceRef.current = source;
        } catch (err) {
            console.error('Failed to initialize Web Audio API: ', err);
        }

        return () => {
            // Cleanup on unmount or stream change
            cleanupAudioNodes();
        };
    }, [stream]);

    const cleanupAudioNodes = () => {
        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (audioContextRef.current) {
            if (audioContextRef.current.state !== 'closed') {
                void audioContextRef.current.close();
            }
            audioContextRef.current = null;
        }
        analyserRef.current = null;
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let resizeId: number;
        const handleResize = () => {
            if (canvas) {
                canvas.width = canvas.parentElement?.clientWidth || 600;
                canvas.height = canvas.parentElement?.clientHeight || 320;
            }
        };

        window.addEventListener('resize', handleResize);
        handleResize();

        const dataArray = new Uint8Array(128);
        const timeDomainArray = new Uint8Array(128);
        let time = 0;

        const render = () => {
            time += 0.05;
            const width = canvas.width;
            const height = canvas.height;
            const centerX = width / 2;
            const centerY = height / 2;

            ctx.clearRect(0, 0, width, height);

            // Get real data or fallback to idle simulator values
            let amplitude = 0;
            const analyser = analyserRef.current;

            if (analyser && isRecording) {
                analyser.getByteFrequencyData(dataArray);
                analyser.getByteTimeDomainData(timeDomainArray);

                // Calculate Root Mean Square (RMS) as real amplitude
                let sumSquared = 0;
                for (let i = 0; i < timeDomainArray.length; i++) {
                    const val = (timeDomainArray[i] - 128) / 128;
                    sumSquared += val * val;
                }
                amplitude = Math.sqrt(sumSquared / timeDomainArray.length);
                // Boost amplitude display threshold slightly
                amplitude = Math.min(amplitude * 2.5, 1);
            } else {
                // Idle breathing simulator
                amplitude = 0.05 + Math.sin(time) * 0.03;
                // Simulate default idle values in frequency array
                for (let i = 0; i < dataArray.length; i++) {
                    dataArray[i] = 10 + Math.sin(time + i * 0.1) * 5;
                }
                // Flat time domain centered around 128
                for (let i = 0; i < timeDomainArray.length; i++) {
                    timeDomainArray[i] = 128 + Math.sin(time * 0.5 + i * 0.2) * 4;
                }
            }

            // Draw horizontal background energy waves
            const wavesCount = isRecording ? 3 : 1;
            for (let w = 0; w < wavesCount; w++) {
                ctx.beginPath();
                ctx.lineWidth = w === 0 ? 2 : 1;
                ctx.strokeStyle = w === 0
                    ? `rgba(0, 255, 157, ${0.1 + amplitude * 0.15})`
                    : `rgba(0, 229, 255, ${0.05 + amplitude * 0.1})`;

                const phaseShift = time * 0.8 + w * 2.0;
                const stretchFactor = 0.015 - w * 0.003;

                for (let x = 0; x < width; x++) {
                    // Flatten standard edges via sine window
                    const edgeDist = Math.sin((x / width) * Math.PI);
                    const idx = Math.floor((x / width) * timeDomainArray.length);
                    const tdValue = (timeDomainArray[idx] - 128) / 128;
                    const y = centerY + tdValue * (50 + w * 20) * (amplitude + 0.1) * edgeDist * Math.sin(x * stretchFactor + phaseShift);

                    if (x === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }
                ctx.stroke();
            }

            // Update rotation speed based on active amplitude
            rotationAngleRef.current += 0.01 + amplitude * 0.03;
            outerRotationRef.current -= 0.005 + amplitude * 0.01;

            // Draw outer rotating HUD ring 1 (Ticks outer ring)
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(outerRotationRef.current);
            ctx.strokeStyle = `rgba(0, 255, 157, ${0.12 + amplitude * 0.2})`;
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 8]);
            ctx.beginPath();
            ctx.arc(0, 0, 140 + amplitude * 12, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();

            // Draw rotating HUD ring 2 (Multi-segmented circular arc)
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(rotationAngleRef.current);
            ctx.strokeStyle = `rgba(0, 229, 255, ${0.2 + amplitude * 0.3})`;
            ctx.lineWidth = 1.5;
            ctx.setLineDash([60, 20, 10, 20, 80, 40]);
            ctx.beginPath();
            ctx.arc(0, 0, 120 + amplitude * 8, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();

            // Emit energy pulse ripple ring while active
            if (isRecording && amplitude > 0.15) {
                ctx.beginPath();
                const pulseRadius = 75 + ((time * 80) % 50);
                const pulseOpacity = Math.max(0, 1 - (pulseRadius - 75) / 50) * 0.3;
                ctx.strokeStyle = `rgba(136, 255, 204, ${pulseOpacity})`;
                ctx.lineWidth = 2;
                ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Draw circular frequency spectrum analyzer columns
            const numBars = 96;
            const baseRadius = 75 + amplitude * 10;
            for (let i = 0; i < numBars; i++) {
                const angle = (i / numBars) * Math.PI * 2;
                const valIndex = Math.floor((i / numBars) * dataArray.length * 0.7);
                const val = dataArray[valIndex] || 0;
                const barHeight = (val / 255) * 45 * (isRecording ? 1.4 : 0.4);

                const x1 = centerX + Math.cos(angle) * baseRadius;
                const y1 = centerY + Math.sin(angle) * baseRadius;
                const x2 = centerX + Math.cos(angle) * (baseRadius + barHeight);
                const y2 = centerY + Math.sin(angle) * (baseRadius + barHeight);

                // Highlight reactive frequency lines
                const rColor = isRecording ? 0 : 0;
                const gColor = isRecording ? 255 : 229;
                const bColor = isRecording ? 157 : 255;
                ctx.strokeStyle = `rgba(${rColor}, ${gColor}, ${bColor}, ${0.3 + (val / 255) * 0.5})`;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }

            // Draw orbiting small neon particles
            particlesRef.current.forEach((p) => {
                p.angle += p.speed * (1 + amplitude * 1.8);
                p.radius = p.baseRadius + amplitude * 22 + Math.sin(time * 0.5 + p.angle) * 4;
                const px = centerX + Math.cos(p.angle) * p.radius;
                const py = centerY + Math.sin(p.angle) * p.radius;
                ctx.fillStyle = p.color;
                ctx.beginPath();
                ctx.arc(px, py, p.size, 0, Math.PI * 2);
                ctx.fill();

                // Dynamic faint trail line connecting particle to center ring for HUD look
                if (isRecording && amplitude > 0.3) {
                    ctx.strokeStyle = `rgba(0, 229, 255, ${0.05 * (p.size / 3)})`;
                    ctx.lineWidth = 0.5;
                    ctx.beginPath();
                    ctx.moveTo(centerX + Math.cos(p.angle) * baseRadius, centerY + Math.sin(p.angle) * baseRadius);
                    ctx.lineTo(px, py);
                    ctx.stroke();
                }
            });

            // Draw center visualizer solid core
            ctx.beginPath();
            ctx.arc(centerX, centerY, 58, 0, Math.PI * 2);
            // Soft breathing or reactive neon solid inner gradient
            const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 60);
            gradient.addColorStop(0, '#07111B');
            gradient.addColorStop(0.7, '#07111B');
            gradient.addColorStop(1, isRecording ? '#00FF9D33' : '#00E5FF22');
            ctx.fillStyle = gradient;

            // Canvas shadow/outer glow based on dynamic RMS volume amplitude
            ctx.shadowBlur = 10 + amplitude * 35;
            ctx.shadowColor = isRecording ? '#00FF9D' : '#00E5FF';
            ctx.fill();
            ctx.shadowBlur = 0; // Turn off shadows for next drawing items

            // Stroke border ring for core
            ctx.strokeStyle = isRecording
                ? `rgba(0, 255, 157, ${0.5 + amplitude * 0.5})`
                : 'rgba(0, 229, 255, 0.3)';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(centerX, centerY, 58, 0, Math.PI * 2);
            ctx.stroke();

            // Render futuristic Microphone icon inside core
            ctx.save();
            ctx.translate(centerX, centerY);

            const iconScale = 1.0 + amplitude * 0.05;
            ctx.scale(iconScale, iconScale);

            ctx.fillStyle = isRecording ? '#00FF9D' : '#e7edf7';

            // Microphone Icon Path geometry
            ctx.beginPath();
            // Mic capsule
            ctx.roundRect(-8, -20, 16, 26, 8);
            ctx.fill();

            // Stand/u-shaped ring
            ctx.strokeStyle = isRecording ? '#00FF9D' : '#e7edf7';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(0, -5, 12, 0, Math.PI, false);
            ctx.stroke();

            // Stand vertical stem and base foot
            ctx.beginPath();
            ctx.moveTo(0, 7);
            ctx.lineTo(0, 16);
            ctx.moveTo(-7, 16);
            ctx.lineTo(7, 16);
            ctx.stroke();

            ctx.restore();

            animationFrameIdRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            window.removeEventListener('resize', handleResize);
            if (animationFrameIdRef.current) {
                cancelAnimationFrame(animationFrameIdRef.current);
            }
        };
    }, [isRecording]);

    return (
        <div className="relative w-full h-[300px] flex items-center justify-center overflow-hidden rounded-xl border border-[rgba(0,255,157,0.06)] bg-[#05070a] shadow-inner">
            {/* Animated radar grid decoration in canvas background */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,229,255,0.03)_0%,rgba(0,0,0,0)_70%)] pointer-events-none" />
            <canvas
                ref={canvasRef}
                onClick={disabled ? undefined : onClick}
                className="block w-full h-full cursor-pointer z-10"
            />
        </div>
    );
}
