import React, { useCallback } from 'react';
import { Upload } from 'lucide-react';
import clsx from 'clsx';

import { ProcessingStatus } from './ProcessingStatus';

interface FileDropZoneProps {
    onFileSelect: (file: File) => void;
    accept?: string;
    label?: string;
    isLoading?: boolean;
    isSuccess?: boolean;
    onViewSchedule?: () => void;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelect, accept, label = "Drop CD Grid or AM Grid here", isLoading = false, isSuccess = false, onViewSchedule }) => {
    const [isDragOver, setIsDragOver] = React.useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        if (!isLoading) setIsDragOver(true);
    }, [isLoading]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);

        if (!isLoading && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onFileSelect(e.dataTransfer.files[0]);
        }
    }, [onFileSelect, isLoading]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (!isLoading && e.target.files && e.target.files.length > 0) {
            onFileSelect(e.target.files[0]);
        }
    }, [onFileSelect, isLoading]);

    if (isLoading || isSuccess) {
        return <ProcessingStatus isSuccess={isSuccess} onViewSchedule={onViewSchedule} />;
    }

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={clsx("drop-zone", isDragOver && "drag-over")}
        >
            <input
                type="file"
                className="hidden"
                id="file-upload"
                accept={accept}
                onChange={handleFileInput}
                style={{ display: 'none' }}
                disabled={isLoading}
            />
            <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', height: '100%' }}>
                <div className="drop-zone-icon">
                    <Upload size={24} />
                </div>
                <p className="drop-zone-label">
                    {label}
                </p>
                <p className="drop-zone-hint">
                    Supports PDF and Excel files. Drag & drop or click to browse.
                </p>
            </label>
        </div>
    );
};
