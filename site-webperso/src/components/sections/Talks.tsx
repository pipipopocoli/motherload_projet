"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";

export const Talks = ({ content }: { content: LocalizedContent['talks'] }) => {
    const { tone } = useTone();

    return (
        <section id="talks" className="py-24 border-t border-forest/5">
            <div className="container mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-16">

                {/* Upcoming */}
                <div>
                    <h3 className="font-mono text-xs uppercase tracking-widest text-brass mb-8 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                        Upcoming
                    </h3>
                    <div className="space-y-8">
                        {content.upcoming.map((talk, i) => (
                            <div key={i} className="group">
                                <div className="text-xl font-serif font-bold text-ink mb-1 group-hover:text-forest transition-colors">
                                    {talk.title}
                                </div>
                                <div className="flex justify-between font-mono text-xs text-muted border-t border-dashed border-gray-300 pt-1 mt-2">
                                    <span>{talk.venue}</span>
                                    <span>{talk.date}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Past */}
                <div>
                    <h3 className="font-mono text-xs uppercase tracking-widest text-muted mb-8">
                        Past
                    </h3>
                    <div className="space-y-8 opacity-60">
                        {content.past.map((talk, i) => (
                            <div key={i}>
                                <div className="text-xl font-serif font-bold text-ink mb-1">
                                    {talk.title}
                                </div>
                                <div className="flex justify-between font-mono text-xs text-muted border-t border-dashed border-gray-300 pt-1 mt-2">
                                    <span>{talk.venue}</span>
                                    <span>{talk.date}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </section>
    );
};
