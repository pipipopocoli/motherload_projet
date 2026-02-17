"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";
import { useScroll, useTransform, motion } from "framer-motion";
import { useRef } from "react";

export const Diagram = () => {
    const { tone } = useTone();
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start end", "end start"]
    });

    const pathLength = useTransform(scrollYProgress, [0.2, 0.5], [0, 1]);
    const opacity = useTransform(scrollYProgress, [0.1, 0.3], [0, 1]);

    return (
        <section id="diagram" ref={ref} className="py-32 bg-paper relative overflow-hidden">
            <div className="container mx-auto px-6 text-center">

                <div className="mb-12 font-mono text-xs uppercase tracking-widest text-brass opacity-60">
                    Logic Flow
                </div>

                <div className="max-w-4xl mx-auto relative">
                    <svg viewBox="0 0 800 200" className="w-full h-auto">
                        <defs>
                            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                                <path d="M0,0 L0,6 L9,3 z" fill="#0E3B2E" />
                            </marker>
                        </defs>

                        {/* Nodes */}
                        <g className="font-serif font-bold text-xl fill-ink">
                            <text x="100" y="100" textAnchor="middle">Evidence</text>
                            <text x="300" y="100" textAnchor="middle">Metrics</text>
                            <text x="500" y="100" textAnchor="middle">Claims</text>
                            <text x="700" y="100" textAnchor="middle">Governance</text>
                        </g>

                        {/* Connecting Lines (Animated) */}
                        <motion.path
                            d="M140,95 Q200,90 260,95"
                            fill="none"
                            stroke="#0E3B2E"
                            strokeWidth="2"
                            markerEnd="url(#arrow)"
                            style={{ pathLength, opacity }}
                        />
                        <motion.path
                            d="M340,95 Q400,100 460,95"
                            fill="none"
                            stroke="#0E3B2E"
                            strokeWidth="2"
                            markerEnd="url(#arrow)"
                            style={{ pathLength, opacity }}
                        />
                        <motion.path
                            d="M540,95 Q600,90 660,95"
                            fill="none"
                            stroke="#B08D57"
                            strokeWidth="2"
                            strokeDasharray="4,4"
                            markerEnd="url(#arrow)"
                            style={{ pathLength, opacity }}
                        />

                        {/* Annotations */}
                        <g className="font-mono text-[10px] fill-muted uppercase tracking-wider">
                            <text x="200" y="80" textAnchor="middle">Corpora</text>
                            <text x="400" y="115" textAnchor="middle">Analysis</text>
                            <text x="600" y="80" textAnchor="middle">Policy</text>
                        </g>
                    </svg>
                </div>

            </div>
        </section>
    );
};
