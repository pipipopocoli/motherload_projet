import { LocalizedContent } from "../types";

export const en: LocalizedContent = {
    hero: {
        tagline: "Regulate the evidence, not the tool.",
        subline: "Philosophy of AI · Ethics · Governance · Data methods",
        proof: ["UQAR", "Evidence-first approach", "Scholar"],
        cta: {
            calm: "See current projects",
            spicy: "See what I'm actually doing"
        }
    },
    now: {
        title: "Now",
        projects: [
            {
                title: "Master's Thesis",
                problem: "LLMs destroy traditional readability metrics, creating linguistic inequity.",
                method: ["Comparative analysis of pre/post ChatGPT corpora", "New metric development"],
                why: "We need tools to detect machine-generated density inequality.",
                status: "Ongoing"
            },
            {
                title: "AI Transparency",
                problem: "Scientific publishing lacks clear standards for AI disclosure.",
                method: ["Policy review of top 20 publishers", "Gap analysis"],
                why: "Trust in science depends on knowing who (or what) wrote it.",
                status: "Ongoing"
            },
            {
                title: "Simuvaction 2026",
                problem: "Bridging the gap between AI technical speed and governance slowness.",
                method: ["Simulation design", "Interdisciplinary coordination"],
                why: "Governance needs to be practiced, not just theorized.",
                status: "Planned"
            },
            {
                title: "Nature of AGI",
                problem: "Defining AGI is a moving target that hampers regulation.",
                method: ["Conceptual analysis", "Literature synthesis"],
                why: "You can't regulate what you can't define.",
                status: "Drafting"
            }
        ]
    },
    research: {
        title: "Research Pillars",
        pillars: [
            { title: "Governance & Responsibility", desc: "Philosophy-anchored policy." },
            { title: "Social Impact & Justice", desc: "Distribution of AI risks." },
            { title: "Mind & Moral Status", desc: "The boundary of subjects." }
        ],
        approach: ["Evidence", "Metrics", "Interpretation", "Governance"]
    },
    projects: {
        title: "Projects",
        items: [
            { category: "Governance", title: "Global AI Index", desc: "Analysis of national AI strategies.", details: "Comparative study of 30+ countries." },
            { category: "Science", title: "Bibliometric Flow", desc: "Mapping citation cartels.", details: "Using Graph theory to find citation rings." },
        ]
    },
    talks: {
        title: "Talks",
        upcoming: [
            { title: "AI & Equity", venue: "OBVIA", date: "April 2026" },
            { title: "Bioethics in the Loop", venue: "NY Bioethics", date: "May 2026" },
        ],
        past: [
            { title: "Student Ethics Colloquium", venue: "UQAR", date: "Oct 2025" }
        ]
    },
    contact: {
        title: "Contact",
        submit: {
            calm: "Send Message",
            spicy: "Launch it"
        }
    },
    nav: {
        now: "Now",
        projects: "Projects",
        research: "Research",
        talks: "Talks",
        contact: "Contact"
    },
    meta: {
        tone_label: "Tone"
    }
};
