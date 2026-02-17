"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";

export const Research = ({ content }: { content: LocalizedContent['research'] }) => {
    const { tone } = useTone();

    return (
        <section id="research" className="py-24 relative overflow-hidden">
            <div className="container mx-auto px-6">

                <div className="max-w-3xl mb-16">
                    <h2 className="text-4xl font-serif font-bold text-forest mb-4">{content.title}</h2>
                    {tone === 'spicy' && (
                        <div className="font-hand text-xl text-brass -rotate-1 ml-2">
                            (The hills I will die on)
                        </div>
                    )}
                </div>

                {/* Pillars */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
                    {content.pillars.map((pillar, i) => (
                        <div key={i} className="relative p-8 border border-forest/20 flex flex-col items-center text-center hover:bg-white/50 transition-colors">
                            <div className="w-12 h-12 mb-6 flex items-center justify-center border border-brass rounded-full text-brass font-serif italic text-2xl">
                                {i + 1}
                            </div>
                            <h3 className="text-xl font-serif font-bold text-ink mb-4">{pillar.title}</h3>
                            <p className="font-serif text-muted italic">{pillar.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Approach Strip */}
                <div className="border-t border-b border-forest/10 py-6">
                    <div className="flex flex-wrap justify-between items-center gap-4 text-sm font-mono uppercase tracking-widest text-forest/80">
                        {content.approach.map((step, i) => (
                            <div key={i} className="flex items-center gap-4">
                                <span>{step}</span>
                                {i < content.approach.length - 1 && (
                                    <span className="text-brass">→</span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </section>
    );
};
