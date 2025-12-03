import React from 'react';
import { Upload, Edit2 } from 'lucide-react';

interface NewDraftOverlayProps {
    onImportClick: () => void;
    onStartClick: () => void;
}

export const NewDraftOverlay: React.FC<NewDraftOverlayProps> = ({ onImportClick, onStartClick }) => {
    return (
        <div className="new-draft-overlay">
            <div className="new-draft-sticky-wrapper">
                <div className="new-draft-content">
                    <div>
                        <h2 className="new-draft-title">New Schedule Draft</h2>
                        <p className="new-draft-subtitle">How would you like to start?</p>
                    </div>

                    <button
                        className="new-draft-btn primary"
                        onClick={onImportClick}
                    >
                        <Upload size={20} />
                        Import Grid
                    </button>

                    <button
                        className="new-draft-btn secondary"
                        onClick={onStartClick}
                    >
                        <Edit2 size={20} />
                        Start Creating Manually
                    </button>
                </div>
            </div>
        </div>
    );
};
