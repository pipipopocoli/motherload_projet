"use client";

import { useTone } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Github, Linkedin, Twitter } from "lucide-react";

export const Header = ({ content, lang }: { content: LocalizedContent, lang: 'en' | 'fr' }) => {
    const { tone, setTone } = useTone();
    const pathname = usePathname();

    return (
        <header className="fixed top-0 left-0 w-full z-50 bg-paper/90 backdrop-blur-sm border-b border-forest/10 transition-colors duration-300">
            <div className="container mx-auto px-6 h-16 flex justify-between items-center">

                {/* Logo */}
                <div className="flex items-center gap-4">
                    <Link href="/" className="font-serif font-bold text-2xl tracking-tighter hover:text-forest transition-colors">
                        OC.
                    </Link>
                    <div className="hidden sm:flex text-[10px] font-mono uppercase tracking-widest text-brass border border-brass px-2 py-0.5 rounded-full">
                        Field Notes
                    </div>
                </div>

                {/* Desktop Nav */}
                <nav className="hidden md:flex gap-6 items-center">
                    {Object.entries(content.nav).map(([key, label]) => (
                        <Link key={key} href={`#${key}`} className="font-mono text-xs uppercase hover:text-forest hover:underline decoration-brass underline-offset-4 transition-all">
                            {label}
                        </Link>
                    ))}
                </nav>

                {/* Controls */}
                <div className="flex items-center gap-6">

                    {/* Tone Slider */}
                    <div className="flex items-center gap-2 font-mono text-[10px] uppercase">
                        <span className={cn("transition-opacity", tone === 'calm' ? "text-forest font-bold" : "opacity-40")}>Calm</span>
                        <button
                            onClick={() => setTone(tone === 'calm' ? 'spicy' : 'calm')}
                            className="w-8 h-4 bg-forest/20 rounded-full relative p-0.5 transition-colors hover:bg-forest/30"
                        >
                            <div className={cn(
                                "w-3 h-3 bg-forest rounded-full transition-transform duration-300",
                                tone === 'spicy' ? "translate-x-4 bg-brass" : "translate-x-0"
                            )} />
                        </button>
                        <span className={cn("transition-opacity", tone === 'spicy' ? "text-brass font-bold" : "opacity-40")}>Spicy</span>
                    </div>

                    {/* Lang Switch */}
                    <div className="flex font-mono text-xs gap-2 border-l border-forest/20 pl-4">
                        <Link href="/" className={cn(lang === 'en' ? "font-bold text-forest" : "opacity-50 hover:opacity-100")}>EN</Link>
                        <Link href="/fr" className={cn(lang === 'fr' ? "font-bold text-forest" : "opacity-50 hover:opacity-100")}>FR</Link>
                    </div>

                </div>

            </div>
        </header>
    );
};
