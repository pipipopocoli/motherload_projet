"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Now = ({ content }: { content: LocalizedContent['now'] }) => {
    const { tone } = useTone();

    return (
        <section id="now" className="py-24 relative border-t border-forest/5">
            <div className="container mx-auto px-6">

                <div className="flex items-baseline justify-between mb-16">
                    <h2 className="text-4xl font-serif font-bold text-forest">{content.title}</h2>
                    <span className="font-mono text-xs text-brass uppercase tracking-widest">Active State</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {content.projects.map((project, i) => (
                        <div key={i} className="group relative bg-white p-6 shadow-sm border border-forest/5 hover:border-forest/20 hover:shadow-md transition-all duration-300 flex flex-col h-full">
                            {/* Status Chip */}
                            <div className="mb-4">
                                <span className={cn(
                                    "px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest border rounded-sm",
                                    project.status === 'Ongoing' || project.status === 'En cours' ? "border-forest text-forest bg-forest/5" : "border-muted text-muted"
                                )}>
                                    {project.status}
                                </span>
                            </div>

                            <h3 className="text-xl font-serif font-bold text-ink mb-3 group-hover:text-forest transition-colors leading-tight">
                                {project.title}
                            </h3>

                            <p className="text-sm font-serif text-ink/80 italic mb-4 min-h-[3em]">
                                "{project.problem}"
                            </p>

                            <ul className="space-y-2 mb-6 flex-grow">
                                {project.method.map((m, j) => (
                                    <li key={j} className="text-xs font-mono text-muted flex gap-2">
                                        <span className="text-brass">›</span> {m}
                                    </li>
                                ))}
                            </ul>

                            {/* Spicy Why */}
                            <div className="pt-4 border-t border-dashed border-gray-200">
                                <p className={cn(
                                    "text-xs font-hand",
                                    tone === 'spicy' ? "text-forest rotate-1" : "text-muted"
                                )}>
                                    <span className="font-bold mr-1">Why:</span> {project.why}
                                </p>
                            </div>

                        </div>
                    ))}
                </div>

            </div>
        </section>
    );
};
