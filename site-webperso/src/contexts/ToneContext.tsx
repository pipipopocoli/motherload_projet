"use client";

import React, { createContext, useContext, useState } from 'react';
import { Tone } from '@/lib/types';

interface ToneContextType {
    tone: Tone;
    setTone: (tone: Tone) => void;
}

const ToneContext = createContext<ToneContextType>({
    tone: 'calm',
    setTone: () => { },
});

export const ToneProvider = ({ children }: { children: React.ReactNode }) => {
    const [tone, setTone] = useState<Tone>('calm');

    return (
        <ToneContext.Provider value={{ tone, setTone }}>
            {children}
        </ToneContext.Provider>
    );
};

export const useTone = () => useContext(ToneContext);
