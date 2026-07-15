'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';

type GlassPanelProps = {
    children: ReactNode;
    className?: string;
    glowColor?: string;
};

export function GlassPanel({ children, className = '', glowColor = 'rgba(0, 255, 157, 0.08)' }: GlassPanelProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`rounded-[18px] border border-[rgba(0,255,157,0.15)] bg-[rgba(11,17,24,0.7)] backdrop-blur-lg p-8 shadow-2xl relative overflow-hidden transition-all duration-300 ${className}`}
            style={{
                boxShadow: `0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 0 10px 0 ${glowColor}`,
            }}
        >
            {/* Corner mechanical accents */}
            <div className="absolute top-0 left-0 w-8 h-[2px] bg-gradient-to-r from-[#00FF9D] to-transparent" />
            <div className="absolute top-0 left-0 w-[2px] h-8 bg-gradient-to-b from-[#00FF9D] to-transparent" />

            <div className="absolute bottom-0 right-0 w-8 h-[2px] bg-gradient-to-l from-[#00E5FF] to-transparent" />
            <div className="absolute bottom-0 right-0 w-[2px] h-8 bg-gradient-to-t from-[#00E5FF] to-transparent" />

            {/* Cyber overlay elements */}
            <div className="absolute top-1.5 right-2 text-[8px] font-mono text-[rgba(0,255,157,0.15)] tracking-widest pointer-events-none select-none">
                AETH_SYS_v2.4
            </div>

            <div className="relative z-10 w-full h-full flex flex-col">
                {children}
            </div>
        </motion.div>
    );
}
