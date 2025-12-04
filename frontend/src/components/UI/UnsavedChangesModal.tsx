import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal } from './Modal';

interface UnsavedChangesModalProps {
    isOpen: boolean;
    onPublish: () => void;
    onDiscard: () => void;
    onCancel: () => void;
}

export const UnsavedChangesModal: React.FC<UnsavedChangesModalProps> = ({
    isOpen,
    onPublish,
    onDiscard,
    onCancel
}) => {
    return (
        <Modal
            isOpen={isOpen}
            onClose={onCancel}
            title="Unsaved Changes"
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
                        className="btn-unsaved btn-unsaved-cancel"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onDiscard}
                        className="btn-unsaved btn-unsaved-discard"
                    >
                        Discard
                    </button>
                    <button
                        onClick={onPublish}
                        className="btn-unsaved btn-unsaved-publish"
                    >
                        Publish
                    </button>
                </div>
            </div>
        </Modal>
    );
};
