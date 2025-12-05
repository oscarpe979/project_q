import React from 'react';

interface ScheduleModalsProps {
    isPublishModalOpen: boolean;
    setIsPublishModalOpen: (isOpen: boolean) => void;
    isDeleteModalOpen: boolean;
    setIsDeleteModalOpen: (isOpen: boolean) => void;
    voyageNumber: string;
    setVoyageNumber: (voyageNumber: string) => void;
    currentVoyageNumber?: string;
    isPublishing: boolean;
    isDeleting: boolean;
    deleteError?: string;
    onPublishConfirm: () => void;
    onDeleteConfirm: () => void;
}

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
        isDeleting,
        deleteError,
        onPublishConfirm,
        onDeleteConfirm
    } = props;

    return (
        <>
            {/* Publish Modal */}
            {isPublishModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content publish-modal-content">
                        <h3 className="publish-modal-header">Publish Schedule</h3>
                        <p className="publish-modal-text">Enter the Voyage Number to publish this schedule.</p>
                        <input
                            type="text"
                            placeholder=""
                            value={voyageNumber}
                            onChange={(e) => setVoyageNumber(e.target.value)}
                            className="voyage-input"
                            autoFocus={!currentVoyageNumber}
                        />
                        <div className="publish-modal-actions">
                            <button className="btn btn-secondary" onClick={() => setIsPublishModalOpen(false)}>Cancel</button>
                            <button className="btn btn-primary" onClick={onPublishConfirm} disabled={isPublishing}>
                                {isPublishing ? 'Publishing...' : 'Publish'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Modal */}
            {isDeleteModalOpen && (
                <div className="modal-overlay">
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
                            <div className="modal-error-text" style={{ color: 'var(--error)', marginTop: '0.5rem', fontSize: '0.9em' }}>
                                {deleteError}
                            </div>
                        )}
                        <div className="modal-actions">
                            <button className="btn btn-secondary" onClick={() => setIsDeleteModalOpen(false)}>Cancel</button>
                            <button className="btn btn-primary btn-danger" onClick={onDeleteConfirm} disabled={isDeleting}>
                                {isDeleting ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
