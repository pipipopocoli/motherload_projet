import { LocalizedContent } from "../types";

export const fr: LocalizedContent = {
    hero: {
        tagline: "Réguler la preuve, pas l'outil.",
        subline: "Philosophie de l'IA · Éthique · Gouvernance · Méthodes de données",
        proof: ["UQAR", "Approche par la preuve", "Scholar"],
        cta: {
            calm: "Voir les projets",
            spicy: "Voir le vrai travail"
        }
    },
    now: {
        title: "En ce moment",
        projects: [
            {
                title: "Mémoire de Maîtrise",
                problem: "Les LLM brisent les métriques de lisibilité traditionnelles.",
                method: ["Analyse comparative de corpus", "Développement de métriques"],
                why: "Il faut détecter l'inégalité de densité générée par machine.",
                status: "En cours"
            },
            {
                title: "Transparence IA",
                problem: "L'édition scientifique manque de normes de divulgation IA.",
                method: ["Revue des politiques éditeurs", "Analyse d'écarts"],
                why: "La confiance scientifique dépend de la transparence.",
                status: "En cours"
            },
            {
                title: "Simuvaction 2026",
                problem: "Combler l'écart entre vitesse technique et lenteur politique.",
                method: ["Design de simulation", "Coordination interdisciplinaire"],
                why: "La gouvernance doit se pratiquer, pas juste se théoriser.",
                status: "Prévu"
            },
            {
                title: "Nature de l'AGI",
                problem: "Définir l'AGI est une cible mouvante.",
                method: ["Analyse conceptuelle", "Synthèse littéraire"],
                why: "On ne peut pas réguler l'indéfini.",
                status: "Rédaction"
            }
        ]
    },
    research: {
        title: "Piliers de Recherche",
        pillars: [
            { title: "Gouvernance & Responsabilité", desc: "Politique ancrée en philo." },
            { title: "Impact Social & Justice", desc: "Distribution des risques IA." },
            { title: "Esprit & Statut Moral", desc: "La frontière des sujets." }
        ],
        approach: ["Preuve", "Métriques", "Interprétation", "Gouvernance"]
    },
    projects: {
        title: "Projets",
        items: [
            { category: "Gouvernance", title: "Index IA Global", desc: "Analyse des stratégies nationales.", details: "Étude comparative." },
            { category: "Science", title: "Flux Bibliométrique", desc: "Cartographie de cartels.", details: "Théorie des graphes." },
        ]
    },
    talks: {
        title: "Conférences",
        upcoming: [
            { title: "IA & Équité", venue: "OBVIA", date: "Avril 2026" },
            { title: "Bioéthique dans la boucle", venue: "NY Bioethics", date: "May 2026" },
        ],
        past: [
            { title: "Colloque étudiant éthique", venue: "UQAR", date: "Oct 2025" }
        ]
    },
    contact: {
        title: "Contact",
        submit: {
            calm: "Envoyer",
            spicy: "Lancer le message"
        }
    },
    nav: {
        now: "Actuel",
        projects: "Projets",
        research: "Recherche",
        talks: "Conférences",
        contact: "Contact"
    },
    meta: {
        tone_label: "Ton"
    }
};
