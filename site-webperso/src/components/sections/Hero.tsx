"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";
import { motion } from "framer-motion";

export const Hero = ({ content }: { content: LocalizedContent['hero'] }) => {
    const { tone } = useTone();

    return (
        <section id="hero" className="min-h-[85vh] flex flex-col justify-center pt-24 pb-12 relative">
            <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12">

                {/* Left: Text */}
                <div className="lg:col-span-8 flex flex-col justify-center">

                    {/* Stamp / Metadata */}
                    <div className="flex items-center gap-3 mb-6 opacity-60 font-mono text-xs uppercase tracking-widest text-brass">
                        <span>Field Notes Vol. 6</span>
                        <span className="w-12 h-[1px] bg-brass"></span>
                        <span>{new Date().getFullYear()}</span>
                    </div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-5xl md:text-7xl font-serif font-bold text-ink mb-6 leading-[1.1] tracking-tight"
                    >
                        {content.tagline.split("evidence").map((part, i) => (
                            i === 0 ? <>{part}<span className="text-forest decoration-wavy decoration-brass/30 underline underline-offset-8">evidence</span></> : part
                        ))}
                    </motion.h1>

                    <p className="text-xl md:text-2xl font-serif text-muted italic mb-10 max-w-2xl leading-relaxed">
                        {content.subline}
                    </p>

                    <div className="flex flex-wrap gap-3 mb-12">
                        {content.proof.map((item, i) => (
                            <span key={i} className="px-3 py-1 border border-forest/20 rounded-full font-mono text-xs text-forest uppercase tracking-wide bg-paper-dark/50">
                                {item}
                            </span>
                        ))}
                    </div>

                    <div className="flex gap-6 items-center">
                        <a href="#now" className="px-6 py-3 bg-forest text-paper font-mono text-sm uppercase tracking-widest hover:bg-forest-light transition-colors shadow-lg shadow-forest/10 hover:shadow-xl hover:-translate-y-0.5 transform duration-200">
                            {tone === 'calm' ? content.cta.calm : content.cta.spicy}
                        </a>
                    </div>

                </div>

                {/* Right: Abstract Visual */}
                <div className="lg:col-span-4 relative hidden lg:block">
                    <div className="absolute inset-0 border-l border-dashed border-forest/20" />

                    {/* Hand Drawn Placeholder Shape */}
                    <svg viewBox="0 0 200 200" className="w-full h-auto opacity-20 rotate-3">
                        <rect x="20" y="20" width="160" height="160" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="5,5" />
                        <circle cx="100" cy="100" r="40" fill="none" stroke="currentColor" strokeWidth="1" />
                    </svg>
                </div>

            </div>
        </section>
    );
};
