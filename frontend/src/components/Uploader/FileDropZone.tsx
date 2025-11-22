import React, { useCallback } from 'react';
import { Upload } from 'lucide-react';
import clsx from 'clsx';

interface FileDropZoneProps {
    onFileSelect: (file: File) => void;
    accept?: string;
    label?: string;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelect, accept, label = "Drop CD Grid or AM Grid here" }) => {
    const [isDragOver, setIsDragOver] = React.useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onFileSelect(e.dataTransfer.files[0]);
        }
    }, [onFileSelect]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            onFileSelect(e.target.files[0]);
        }
    }, [onFileSelect]);

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={clsx(
                "border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer group",
                isDragOver
                    ? "border-blue-500 bg-blue-50"
                    : "border-[var(--border-medium)] hover:border-[var(--text-secondary)] hover:bg-white/50"
            )}
        >
            <input
                type="file"
                className="hidden"
                id="file-upload"
                accept={accept}
                onChange={handleFileInput}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center w-full h-full">
                <div className={clsx(
                    "h-12 w-12 rounded-full flex items-center justify-center mb-4 transition-colors",
                    isDragOver ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-500 group-hover:bg-gray-200"
                )}>
                    <Upload size={24} />
                </div>
                <p className="text-sm font-medium text-[var(--text-primary)] mb-1">
                    {label}
                </p>
                <p className="text-xs text-[var(--text-secondary)] text-center max-w-xs">
                    Supports PDF and Excel files. Drag & drop or click to browse.
                </p>
            </label>
        </div>
    );
};
