import React, { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import { Check } from 'lucide-react';

import { COLORS } from '../../../utils/eventColors';

const PRESET_COLORS = [
    { name: 'Red', value: COLORS.PRODUCTION_SHOW_1 },
    { name: 'Blue', value: COLORS.PRODUCTION_SHOW_2 },
    { name: 'Purple', value: COLORS.PRODUCTION_SHOW_3 },
    { name: 'Teal', value: COLORS.HEADLINER },
    { name: 'Light Purple', value: COLORS.MOVIE },
    { name: 'Orange', value: COLORS.GAME_SHOW },
    { name: 'Light Blue', value: COLORS.ACTIVITY },
    { name: 'Green', value: COLORS.MUSIC },
    { name: 'Yellow', value: COLORS.PARTY },
    { name: 'Pink', value: COLORS.COMEDY },
    { name: 'Grey', value: COLORS.OTHER },
];

interface ColorSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    triggerRef: React.RefObject<any>;
    currentColor?: string;
    onSelect: (color: string) => void;
}

export const ColorSelector: React.FC<ColorSelectorProps> = ({
    isOpen,
    onClose,
    triggerRef,
    currentColor,
    onSelect,
}) => {
    const popoverRef = useRef<HTMLDivElement>(null);
    const [position, setPosition] = useState({ top: 0, left: 0 });

    useEffect(() => {
        if (isOpen && triggerRef.current) {
            const rect = triggerRef.current.getBoundingClientRect();
            setPosition({
                top: rect.bottom + 4,
                left: rect.left,
            });
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return createPortal(
        <>
            {/* Transparent backdrop to catch clicks and prevent grid interaction */}
            <div
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    zIndex: 9998, // Below popup (9999)
                    cursor: 'default',
                    background: 'transparent' // Invisible
                }}
                onMouseDown={(e) => {
                    e.stopPropagation();
                    e.preventDefault(); // Prevent focus change or other default behaviors
                    onClose();
                }}
            />

            <div
                ref={popoverRef}
                className="color-selector-popup"
                style={{
                    top: position.top,
                    left: position.left,
                    minWidth: '200px',
                    // Default behavior might push it off screen, but relying on body portal helps. 
                    // Could add boundary check later if needed.
                }}
                onMouseDown={(e) => e.stopPropagation()} // Prevent clicks inside popup from closing or bubbling
            >
                <div className="color-selector-header">
                    SELECT COLOR
                </div>

                <div className="color-grid">
                    {PRESET_COLORS.map((color) => (
                        <button
                            key={color.value}
                            onClick={(e) => {
                                e.stopPropagation(); // Stop propagation
                                onSelect(color.value);
                                onClose();
                            }}
                            className={clsx(
                                "color-btn",
                                currentColor === color.value && "active"
                            )}
                            style={{ backgroundColor: color.value }}
                            title={color.name}
                        >
                            {currentColor === color.value && <Check size={14} className="text-white drop-shadow-md" />}
                        </button>
                    ))}
                </div>
            </div>
        </>,
        document.body
    );
};
