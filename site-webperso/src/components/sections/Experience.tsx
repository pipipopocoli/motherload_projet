"use client";

export const Experience = () => {
    return (
        <section id="experience" className="py-24 bg-paper-dark/20">
            <div className="container mx-auto px-6 max-w-2xl">

                <h2 className="text-3xl font-serif font-bold text-forest mb-12">Experience</h2>

                <div className="space-y-12 border-l border-forest/10 ml-3 pl-8 relative">

                    {/* UQAR Master's */}
                    <div className="relative">
                        <div className="absolute -left-[37px] top-1.5 w-3 h-3 border border-forest bg-paper rounded-full"></div>
                        <div className="font-mono text-xs text-brass mb-1">2024 — Present</div>
                        <div className="text-xl font-serif font-bold text-ink">MSc Student</div>
                        <div className="text-sm font-mono text-muted uppercase tracking-wide">UQAR</div>
                    </div>

                    {/* Previous (Placeholder) */}
                    <div className="relative opacity-60">
                        <div className="absolute -left-[37px] top-1.5 w-3 h-3 border border-muted bg-paper rounded-full"></div>
                        <div className="font-mono text-xs text-muted mb-1">2020 — 2024</div>
                        <div className="text-xl font-serif font-bold text-ink">Previous Role</div>
                        <div className="text-sm font-mono text-muted uppercase tracking-wide">Institution</div>
                    </div>

                </div>

            </div>
        </section>
    );
};
