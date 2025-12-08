import React from 'react';

interface BackdropProps {
    onClose?: () => void;
    zIndex?: number;
    invisible?: boolean;
    className?: string;
}

export const Backdrop: React.FC<BackdropProps> = ({
    onClose,
    zIndex = 9998,
    invisible = true,
    className
}) => {
    return (
        <div
            className={className}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: zIndex,
                cursor: 'default',
                backgroundColor: invisible ? 'transparent' : 'rgba(0, 0, 0, 0.4)',
                // Ensure it catches all pointers
                touchAction: 'none'
            }}
            onPointerDown={(e) => {
                e.stopPropagation();
                if (onClose) onClose();
            }}
            onMouseDown={(e) => e.stopPropagation()}
        />
    );
};
