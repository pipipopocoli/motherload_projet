export type Tone = 'calm' | 'spicy';

export interface ToneString {
    calm: string;
    spicy: string;
}

export type LocalizedContent = {
    hero: {
        tagline: string;
        subline: string;
        proof: string[];
        cta: ToneString;
    };
    now: {
        title: string;
        projects: {
            title: string;
            problem: string;
            method: string[];
            why: string;
            status: string;
        }[];
    };
    research: {
        title: string;
        pillars: {
            title: string;
            desc: string;
        }[];
        approach: string[];
    };
    projects: {
        title: string;
        items: {
            category: string;
            title: string;
            desc: string;
            details: string;
        }[];
    };
    talks: {
        title: string;
        upcoming: { title: string; venue: string; date: string }[];
        past: { title: string; venue: string; date: string }[];
    }
    contact: {
        title: string;
        submit: ToneString;
    };
    nav: {
        now: string;
        projects: string;
        research: string;
        talks: string;
        contact: string;
    };
    meta: {
        tone_label: string;
    }
};
