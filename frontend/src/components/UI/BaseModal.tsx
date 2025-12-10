import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface BaseModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    disableEnterKey?: boolean; // Allow child components to handle Enter themselves
}

export const BaseModal: React.FC<BaseModalProps> = ({ isOpen, onClose, title, children, disableEnterKey = false }) => {
    // Handle Enter key to close modal (for confirmation modals)
    useEffect(() => {
        if (!isOpen || disableEnterKey) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown, { capture: true });
        return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
    }, [isOpen, onClose, disableEnterKey]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            {/* Backdrop click handler */}
            <div
                className="modal-backdrop-click"
                onPointerDown={onClose}
            ></div>

            {/* Content */}
            <div className="modal-content">
                <div className="modal-header">
                    <h3 className="modal-title">{title}</h3>
                    <button
                        onClick={onClose}
                        className="modal-close-btn"
                    >
                        <X size={20} />
                    </button>
                </div>
                {children}
            </div>
        </div>
    );
};
