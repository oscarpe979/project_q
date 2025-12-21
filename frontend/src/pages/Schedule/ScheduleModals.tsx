import React, { useEffect, useState, useCallback } from 'react';

interface ScheduleModalsProps {
    isPublishModalOpen: boolean;
    setIsPublishModalOpen: (isOpen: boolean) => void;
    isDeleteModalOpen: boolean;
    setIsDeleteModalOpen: (isOpen: boolean) => void;
    voyageNumber: string;
    setVoyageNumber: (voyageNumber: string) => void;
    currentVoyageNumber?: string;
    isPublishing: boolean;
    publishError?: string;
    isDeleting: boolean;
    deleteError?: string;
    onPublishConfirm: () => void;
    onDeleteConfirm: () => void;
    isPublishAsMode?: boolean;
}

type PublishFocus = 'cancel' | 'publish';
type DeleteFocus = 'cancel' | 'delete';

export const ScheduleModals: React.FC<ScheduleModalsProps> = (props) => {
    const {
        isPublishModalOpen,
        setIsPublishModalOpen,
        isDeleteModalOpen,
        setIsDeleteModalOpen,
        voyageNumber,
        setVoyageNumber,
        currentVoyageNumber,
        isPublishing,
        publishError,
        isDeleting,
        deleteError,
        onPublishConfirm,
        onDeleteConfirm,
        isPublishAsMode
    } = props;

    // Focus state for publish modal buttons
    const [publishFocus, setPublishFocus] = useState<PublishFocus>('publish');
    // Focus state for delete modal buttons
    const [deleteFocus, setDeleteFocus] = useState<DeleteFocus>('cancel');

    // Reset focus when modals open
    useEffect(() => {
        if (isPublishModalOpen) setPublishFocus('publish');
    }, [isPublishModalOpen]);

    useEffect(() => {
        if (isDeleteModalOpen) setDeleteFocus('cancel');
    }, [isDeleteModalOpen]);

    const handlePublishAction = useCallback(() => {
        if (publishFocus === 'cancel') {
            setIsPublishModalOpen(false);
        } else if (!isPublishing) {
            onPublishConfirm();
        }
    }, [publishFocus, setIsPublishModalOpen, isPublishing, onPublishConfirm]);

    const handleDeleteAction = useCallback(() => {
        if (deleteFocus === 'cancel') {
            setIsDeleteModalOpen(false);
        } else if (!isDeleting) {
            onDeleteConfirm();
        }
    }, [deleteFocus, setIsDeleteModalOpen, isDeleting, onDeleteConfirm]);

    // Keyboard navigation for publish modal
    useEffect(() => {
        if (!isPublishModalOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || (e.key === 'Tab')) {
                e.preventDefault();
                setPublishFocus(prev => prev === 'cancel' ? 'publish' : 'cancel');
            } else if (e.key === 'Enter') {
                e.preventDefault();
                handlePublishAction();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isPublishModalOpen, handlePublishAction]);

    // Keyboard navigation for delete modal
    useEffect(() => {
        if (!isDeleteModalOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || (e.key === 'Tab')) {
                e.preventDefault();
                setDeleteFocus(prev => prev === 'cancel' ? 'delete' : 'cancel');
            } else if (e.key === 'Enter') {
                e.preventDefault();
                handleDeleteAction();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isDeleteModalOpen, handleDeleteAction]);

    return (
        <>
            {/* Publish Modal */}
            {isPublishModalOpen && (
                <div className="modal-overlay">
                    <div
                        className="modal-backdrop-click"
                        onPointerDown={() => setIsPublishModalOpen(false)}
                    />
                    <div className="modal-content publish-modal-content">
                        <h3 className="publish-modal-header">
                            {isPublishAsMode ? 'Publish As' : 'Publish Schedule'}
                        </h3>
                        <p className="publish-modal-text">
                            {isPublishAsMode
                                ? 'Enter a new Voyage Number to save a copy of this schedule.'
                                : 'Enter the Voyage Number to publish this schedule.'}
                        </p>
                        <input
                            type="text"
                            placeholder=""
                            value={voyageNumber}
                            onChange={(e) => setVoyageNumber(e.target.value)}
                            className="voyage-input"
                            autoFocus={isPublishAsMode || !currentVoyageNumber}
                        />
                        {publishError && (
                            <div className="modal-error-text">
                                {publishError}
                            </div>
                        )}
                        <div className="publish-modal-actions">
                            <button
                                className={`btn btn-secondary ${publishFocus === 'cancel' ? 'btn-focused' : ''}`}
                                onClick={() => setIsPublishModalOpen(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className={`btn btn-primary ${publishFocus === 'publish' ? 'btn-focused' : ''}`}
                                onClick={onPublishConfirm}
                                disabled={isPublishing}
                            >
                                {isPublishing ? 'Publishing...' : 'Publish'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Modal */}
            {isDeleteModalOpen && (
                <div className="modal-overlay">
                    <div
                        className="modal-backdrop-click"
                        onPointerDown={() => setIsDeleteModalOpen(false)}
                    />
                    <div className="modal-content modal-content-delete">
                        <h3 className="delete-modal-header">Delete Schedule</h3>
                        <p className="delete-modal-text">
                            You are about to delete the <strong>{currentVoyageNumber || 'current'}</strong> schedule.
                            <br />
                            Please confirm the Voyage Number to proceed.
                        </p>
                        <input
                            type="text"
                            placeholder=""
                            value={voyageNumber}
                            onChange={(e) => setVoyageNumber(e.target.value)}
                            className="delete-voyage-input"
                            autoFocus
                        />
                        {deleteError && (
                            <div className="modal-error-text">
                                {deleteError}
                            </div>
                        )}
                        <div className="modal-actions">
                            <button
                                className={`btn btn-secondary ${deleteFocus === 'cancel' ? 'btn-focused' : ''}`}
                                onClick={() => setIsDeleteModalOpen(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className={`btn btn-primary btn-danger ${deleteFocus === 'delete' ? 'btn-focused-danger' : ''}`}
                                onClick={onDeleteConfirm}
                                disabled={isDeleting}
                            >
                                {isDeleting ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
