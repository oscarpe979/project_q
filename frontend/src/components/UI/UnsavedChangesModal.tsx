import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';
import { BaseModal } from './BaseModal';

interface UnsavedChangesModalProps {
    isOpen: boolean;
    onPublish: () => void;
    onDiscard: () => void;
    onCancel: () => void;
}

type FocusedButton = 'cancel' | 'discard' | 'publish';

export const UnsavedChangesModal: React.FC<UnsavedChangesModalProps> = ({
    isOpen,
    onPublish,
    onDiscard,
    onCancel
}) => {
    const [focusedButton, setFocusedButton] = useState<FocusedButton>('cancel');

    // Reset focus when modal opens
    useEffect(() => {
        if (isOpen) {
            setFocusedButton('cancel');
        }
    }, [isOpen]);

    const handleAction = useCallback(() => {
        switch (focusedButton) {
            case 'cancel': onCancel(); break;
            case 'discard': onDiscard(); break;
            case 'publish': onPublish(); break;
        }
    }, [focusedButton, onCancel, onDiscard, onPublish]);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const buttons: FocusedButton[] = ['cancel', 'discard', 'publish'];

        const handleKeyDown = (e: KeyboardEvent) => {
            const currentIndex = buttons.indexOf(focusedButton);

            if (e.key === 'ArrowRight' || (e.key === 'Tab' && !e.shiftKey)) {
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % buttons.length;
                setFocusedButton(buttons[nextIndex]);
            } else if (e.key === 'ArrowLeft' || (e.key === 'Tab' && e.shiftKey)) {
                e.preventDefault();
                const prevIndex = (currentIndex - 1 + buttons.length) % buttons.length;
                setFocusedButton(buttons[prevIndex]);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                e.stopImmediatePropagation();
                handleAction();
            }
        };

        window.addEventListener('keydown', handleKeyDown, { capture: true });
        return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
    }, [isOpen, focusedButton, handleAction]);

    return (
        <BaseModal
            isOpen={isOpen}
            onClose={onCancel}
            title="Unsaved Changes"
            disableEnterKey={true}
        >
            <div className="unsaved-changes-content">
                <div className="unsaved-body">
                    <div className="unsaved-icon-wrapper">
                        <AlertTriangle size={24} />
                    </div>
                    <p className="unsaved-text">
                        You have unsaved changes. Do you want to publish them before leaving?
                    </p>
                </div>

                <div className="unsaved-actions">
                    <button
                        onClick={onCancel}
                        className={`btn-unsaved btn-unsaved-cancel ${focusedButton === 'cancel' ? 'btn-focused' : ''}`}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onDiscard}
                        className={`btn-unsaved btn-unsaved-discard ${focusedButton === 'discard' ? 'btn-focused-danger' : ''}`}
                    >
                        Discard
                    </button>
                    <button
                        onClick={onPublish}
                        className={`btn-unsaved btn-unsaved-publish ${focusedButton === 'publish' ? 'btn-focused' : ''}`}
                    >
                        Publish
                    </button>
                </div>
            </div>
        </BaseModal>
    );
};
