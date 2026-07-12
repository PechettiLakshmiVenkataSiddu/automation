'use client';

import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

const smoothEase = [0.16, 1, 0.3, 1] as const;

export default function Template({ children }: { children: ReactNode }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: smoothEase }}
        >
            {children}
        </motion.div>
    );
}