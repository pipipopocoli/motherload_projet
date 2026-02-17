"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";

export const Contact = ({ content }: { content: LocalizedContent['contact'] }) => {
    const { tone } = useTone();

    return (
        <section id="contact" className="py-32 border-t-4 border-forest bg-paper">
            <div className="container mx-auto px-6 max-w-xl">

                <div className="text-center mb-12">
                    <h2 className="text-4xl font-serif font-bold text-forest mb-4">{content.title}</h2>
                    <p className="font-mono text-xs text-muted">
                        olivier.cloutier@ucar.ca
                    </p>
                </div>

                <form action="https://formspree.io/f/mnnjkgqk" method="POST" className="space-y-6">
                    <div>
                        <label className="block font-mono text-[10px] uppercase tracking-widest text-brass mb-2">Topic</label>
                        <select name="topic" className="w-full bg-transparent border-b border-forest/20 py-2 font-serif text-xl focus:border-forest outline-none rounded-none">
                            <option>Collaboration</option>
                            <option>Speaking</option>
                            <option>Other</option>
                        </select>
                    </div>

                    <div>
                        <label className="block font-mono text-[10px] uppercase tracking-widest text-brass mb-2">Message</label>
                        <textarea name="message" rows={4} className="w-full bg-transparent border-b border-forest/20 py-2 font-serif text-xl focus:border-forest outline-none resize-none rounded-none placeholder:text-muted/20" placeholder="..."></textarea>
                    </div>

                    <button type="submit" className="w-full py-4 bg-forest text-paper font-mono text-sm uppercase tracking-widest hover:bg-brass transition-colors mt-8">
                        {tone === 'calm' ? content.submit.calm : content.submit.spicy}
                    </button>
                </form>

                {/* Socials Row */}
                <div className="flex justify-center gap-6 mt-16 opacity-50 hover:opacity-100 transition-opacity grayscale hover:grayscale-0">
                    {/* Simple placeholders as requested */}
                    <div className="w-5 h-5 bg-ink/20 hover:bg-forest transition-colors rounded-sm cursor-pointer" title="Scholar" />
                    <div className="w-5 h-5 bg-ink/20 hover:bg-forest transition-colors rounded-sm cursor-pointer" title="LinkedIn" />
                    <div className="w-5 h-5 bg-ink/20 hover:bg-forest transition-colors rounded-sm cursor-pointer" title="GitHub" />
                    <div className="w-5 h-5 bg-ink/20 hover:bg-forest transition-colors rounded-sm cursor-pointer" title="X" />
                </div>

            </div>
        </section>
    );
};
