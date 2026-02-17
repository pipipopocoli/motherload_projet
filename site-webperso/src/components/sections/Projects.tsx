"use client";

import { LocalizedContent } from "@/lib/types";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus } from "lucide-react";

export const Projects = ({ content }: { content: LocalizedContent['projects'] }) => {
    return (
        <section id="projects" className="py-24 bg-paper-dark/30">
            <div className="container mx-auto px-6 max-w-4xl">

                <h2 className="text-4xl font-serif font-bold text-forest mb-12 border-b border-forest/10 pb-4">
                    {content.title}
                </h2>

                <div className="space-y-4">
                    {content.items.map((item, i) => (
                        <ProjectItem key={i} item={item} />
                    ))}
                </div>

            </div>
        </section>
    );
};

const ProjectItem = ({ item }: { item: LocalizedContent['projects']['items'][0] }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="border border-forest/10 bg-paper hover:border-forest/30 transition-colors">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-4 text-left group"
            >
                <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-8">
                    <span className="font-mono text-xs uppercase text-brass w-24">{item.category}</span>
                    <span className="font-serif font-bold text-lg text-ink group-hover:text-forest transition-colors">
                        {item.title}
                    </span>
                    <span className="text-sm text-muted hidden md:block opacity-60">
                        {item.desc}
                    </span>
                </div>
                <div className="text-forest/50 group-hover:text-forest">
                    {isOpen ? <Minus size={16} /> : <Plus size={16} />}
                </div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 pt-0 pl-4 md:pl-36 text-sm font-serif text-muted leading-relaxed">
                            {item.details}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
