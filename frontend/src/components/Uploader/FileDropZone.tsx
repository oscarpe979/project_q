import React, { useCallback } from 'react';
import { Upload } from 'lucide-react';
import clsx from 'clsx';

interface FileDropZoneProps {
    onFileSelect: (file: File) => void;
    accept?: string;
    label?: string;
    isLoading?: boolean;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelect, accept, label = "Drop CD Grid or AM Grid here", isLoading = false }) => {
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

    if (isLoading) {
        return (
            <div className="drop-zone" style={{ cursor: 'default', borderColor: 'var(--text-accent)', backgroundColor: 'rgba(37, 99, 235, 0.05)' }}>
                <div className="drop-zone-icon" style={{ color: 'var(--text-accent)', backgroundColor: 'rgba(37, 99, 235, 0.1)' }}>
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-current"></div>
                </div>
                <p className="drop-zone-label" style={{ color: 'var(--text-accent)' }}>
                    Analyzing PDF with Gemini...
                </p>
                <p className="drop-zone-hint">
                    This may take up to a minute.
                </p>
            </div>
        );
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
