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
            <div className="unsaved-changes-content" style={{ padding: '0 20px 20px' }}>
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '16px',
                    marginBottom: '24px'
                }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        backgroundColor: '#FEF3C7',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#D97706'
                    }}>
                        <AlertTriangle size={24} />
                    </div>
                    <p style={{
                        textAlign: 'center',
                        color: '#4B5563',
                        fontSize: '15px',
                        lineHeight: '1.5',
                        margin: 0
                    }}>
                        You have unsaved changes. Do you want to publish them before leaving?
                    </p>
                </div>

                <div style={{
                    display: 'flex',
                    gap: '12px',
                    justifyContent: 'center'
                }}>
                    <button
                        onClick={onCancel}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '8px',
                            border: '1px solid #E5E7EB',
                            background: 'white',
                            color: '#374151',
                            fontWeight: 500,
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onDiscard}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '8px',
                            border: '1px solid #FCA5A5',
                            background: '#FEF2F2',
                            color: '#DC2626',
                            fontWeight: 500,
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        Discard
                    </button>
                    <button
                        onClick={onPublish}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '8px',
                            border: 'none',
                            background: '#2563EB',
                            color: 'white',
                            fontWeight: 500,
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        Publish
                    </button>
                </div>
            </div>
        </Modal>
    );
};
