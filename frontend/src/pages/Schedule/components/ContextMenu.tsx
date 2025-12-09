import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

export interface ContextMenuItem {
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    disabled?: boolean;
    danger?: boolean;
    separator?: boolean;
}

interface ContextMenuProps {
    position: { x: number; y: number } | null;
    items: ContextMenuItem[];
    onClose: () => void;
}

export const ContextMenu: React.FC<ContextMenuProps> = ({ position, items, onClose }) => {
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                onClose();
            }
        };

        const handleScroll = () => {
            onClose();
        };

        if (position) {
            document.addEventListener('mousedown', handleClickOutside);
            document.addEventListener('scroll', handleScroll, true);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('scroll', handleScroll, true);
        };
    }, [position, onClose]);

    if (!position) return null;

    return createPortal(
        <div
            ref={menuRef}
            className="context-menu-container"
            style={{
                top: position.y,
                left: position.x,
            }}
        >
            <div className="context-menu-items">
                {items.map((item, index) => {
                    if (item.separator) {
                        return <div key={index} className="context-menu-separator" />;
                    }

                    return (
                        <button
                            key={index}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (!item.disabled) {
                                    item.onClick();
                                    onClose();
                                }
                            }}
                            disabled={item.disabled}
                            className={`context-menu-item ${item.disabled ? 'disabled' : ''} ${item.danger ? 'danger' : ''}`}
                        >
                            {item.icon && (
                                <span className="context-menu-icon">
                                    {item.icon}
                                </span>
                            )}
                            <span className="context-menu-label">{item.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>,
        document.body
    );
};
