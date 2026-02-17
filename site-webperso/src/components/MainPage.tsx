"use client";

import { ToneProvider } from "@/contexts/ToneContext";
import { LocalizedContent } from "@/lib/types";
import { Header } from "./Header";
import { StickFigure } from "./StickFigure";
import { Hero } from "./sections/Hero";
import { Now } from "./sections/Now";
import { Projects } from "./sections/Projects";
import { Research } from "./sections/Research";
import { Diagram } from "./sections/Diagram";
import { Talks } from "./sections/Talks";
import { Experience } from "./sections/Experience";
import { Contact } from "./sections/Contact";

export const MainPage = ({ content, lang }: { content: LocalizedContent, lang: 'en' | 'fr' }) => {
    return (
        <ToneProvider>
            <Header content={content} lang={lang} />
            <StickFigure />

            <main className="relative z-10">
                <Hero content={content.hero} />
                <Now content={content.now} />
                <Projects content={content.projects} />
                <Research content={content.research} />
                <Diagram />
                <Talks content={content.talks} />
                <Experience />
                <Contact content={content.contact} />
            </main>

        </ToneProvider>
    );
};
