"use client";

import { useScroll, motion, useSpring, useTransform } from "framer-motion";
import { useEffect, useState } from "react";

export const StickFigure = () => {
    const { scrollYProgress } = useScroll();
    const y = useSpring(useTransform(scrollYProgress, [0, 1], [0, 100]), {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001
    });

    const [windowHeight, setWindowHeight] = useState(0);

    useEffect(() => {
        setWindowHeight(window.innerHeight);
    }, []);

    return (
        <motion.div
            className="fixed left-4 md:left-8 top-24 z-40 hidden md:block pointer-events-none"
            style={{ top: useTransform(scrollYProgress, [0, 1], ["10vh", "85vh"]) }}
        >
            <svg width="60" height="120" viewBox="0 0 60 120" className="stroke-ink fill-none stroke-2 overflow-visible">
                {/* Head */}
                <circle cx="30" cy="20" r="15" />
                {/* Body */}
                <line x1="30" y1="35" x2="30" y2="80" />
                {/* Arms - Waving/Balancing */}
                <motion.path
                    d="M30 45 L10 60"
                    style={{ rotate: useTransform(scrollYProgress, [0, 1], [0, -20]) }}
                />
                <motion.path
                    d="M30 45 L50 60"
                    style={{ rotate: useTransform(scrollYProgress, [0, 1], [0, 20]) }}
                />
                {/* Legs - Walking */}
                <motion.path
                    d="M30 80 L15 110"
                    style={{ skewX: useTransform(scrollYProgress, [0, 0.5, 1], [0, 10, -10]) }}
                />
                <motion.path
                    d="M30 80 L45 110"
                    style={{ skewX: useTransform(scrollYProgress, [0, 0.5, 1], [0, -10, 10]) }}
                />
            </svg>
        </motion.div>
    );
};
