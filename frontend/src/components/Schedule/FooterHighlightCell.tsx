import React, { useState, useRef, useEffect } from 'react';
import { Edit2 } from 'lucide-react';
import { format } from 'date-fns';

interface FooterHighlightCellProps {
    venue: string;
    date: Date;
    show?: { title: string; time: string };
    onUpdate: (venue: string, date: string, title: string, time: string) => void;
}

export const FooterHighlightCell: React.FC<FooterHighlightCellProps> = ({ venue, date, show, onUpdate }) => {
    const [isEditingTime, setIsEditingTime] = useState(false);
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [editTime, setEditTime] = useState(show ? show.time : '');
    const [editTitle, setEditTitle] = useState(show ? show.title : '');
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (show) {
            setEditTime(show.time);
            setEditTitle(show.title);
        } else {
            setEditTime('');
            setEditTitle('');
        }
    }, [show]);

    const handleBlurTime = () => {
        timeoutRef.current = setTimeout(() => {
            setIsEditingTime(false);
            // We trigger update on every blur to save progress
            const newTitle = editTitle.trim();
            const newTime = editTime.trim();
            if (newTitle || newTime) {
                onUpdate(venue, format(date, 'yyyy-MM-dd'), newTitle, newTime);
            } else {
                onUpdate(venue, format(date, 'yyyy-MM-dd'), '', '');
            }
        }, 50);
    };

    const handleBlurTitle = () => {
        timeoutRef.current = setTimeout(() => {
            setIsEditingTitle(false);
            const newTitle = editTitle.trim();
            const newTime = editTime.trim();
            if (newTitle || newTime) {
                onUpdate(venue, format(date, 'yyyy-MM-dd'), newTitle, newTime);
            } else {
                onUpdate(venue, format(date, 'yyyy-MM-dd'), '', '');
            }
        }, 50);
    };

    const handleKeyDownTime = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.currentTarget.blur();
        } else if (e.key === 'Escape') {
            setEditTime(show ? show.time : '');
            setIsEditingTime(false);
        }
    };

    const handleKeyDownTitle = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.currentTarget.blur();
        } else if (e.key === 'Escape') {
            setEditTitle(show ? show.title : '');
            setIsEditingTitle(false);
        }
    };

    const handleCreate = () => {
        setIsEditingTime(true);
        setIsEditingTitle(true);
    };

    if (!show || (!show.title && !show.time)) {
        // Empty state: Show dash with a single pencil to "create"
        if (isEditingTime || isEditingTitle) {
            // If we are editing (e.g. just clicked create), show both inputs
            return (
                <div className="venue-day-cell group relative flex flex-col gap-1 justify-center items-center">
                    {isEditingTime ? (
                        <input
                            type="text"
                            className="glass-input"
                            placeholder="Time"
                            value={editTime}
                            onChange={(e) => setEditTime(e.target.value)}
                            onBlur={handleBlurTime}
                            onKeyDown={handleKeyDownTime}
                            onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)}
                            autoFocus
                            style={{
                                width: `calc(${editTime.length}ch + 3rem)`,
                                minWidth: '100%',
                                textTransform: 'inherit',
                                lineHeight: 'inherit',
                                margin: 0,
                                height: 'auto',
                                boxSizing: 'border-box'
                            } as React.CSSProperties}
                        />
                    ) : (
                        <div className="venue-show-time" onClick={() => setIsEditingTime(true)}>{editTime || 'Time'}</div>
                    )}

                    {isEditingTitle ? (
                        <input
                            type="text"
                            className="glass-input"
                            placeholder="Title"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={handleBlurTitle}
                            onKeyDown={handleKeyDownTitle}
                            onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)}
                            style={{
                                width: `calc(${editTitle.length}ch + 3rem)`,
                                minWidth: '100%',
                                textTransform: 'inherit',
                                lineHeight: 'inherit',
                                margin: 0,
                                height: 'auto',
                                boxSizing: 'border-box'
                            } as React.CSSProperties}
                        />
                    ) : (
                        <div className="venue-show-title" onClick={() => setIsEditingTitle(true)}>{editTitle || 'Title'}</div>
                    )}
                </div>
            );
        }

        return (
            <div className="venue-day-cell group relative">
                <div className="venue-no-show relative inline-block group-title-wrapper">
                    <span>-</span>
                    <span className="pencil-spacer">
                        <span
                            role="button"
                            className="edit-icon-btn"
                            onPointerDown={(e) => e.stopPropagation()}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleCreate();
                            }}
                        >
                            <Edit2 size={10} className="edit-icon-svg" />
                        </span>
                    </span>
                </div>
            </div>
        );
    }

    return (
        <div className="venue-day-cell group relative flex flex-col justify-center items-center">
            {/* Time Section */}
            <div className="venue-show-time relative flex justify-center items-center" style={{ minHeight: '1.2em' }}>
                <div className={`relative inline-block group-time-wrapper ${isEditingTime ? 'invisible' : ''}`}>
                    <span>{show.time}</span>
                    <span className="pencil-spacer">
                        <span
                            role="button"
                            className="edit-icon-btn"
                            onPointerDown={(e) => e.stopPropagation()}
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsEditingTime(true);
                            }}
                        >
                            <Edit2 size={10} className="edit-icon-svg" />
                        </span>
                    </span>
                </div>
                {isEditingTime && (
                    <div className="absolute inset-0 flex items-center justify-center z-50">
                        <input
                            type="text"
                            className="glass-input"
                            value={editTime}
                            onChange={(e) => setEditTime(e.target.value)}
                            onBlur={handleBlurTime}
                            onKeyDown={handleKeyDownTime}
                            onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)}
                            autoFocus
                            style={{
                                width: `calc(${editTime.length}ch + 3rem)`,
                                minWidth: '100%',
                                textTransform: 'inherit',
                                lineHeight: 'inherit',
                                margin: 0,
                                height: 'auto',
                                boxSizing: 'border-box'
                            } as React.CSSProperties}
                        />
                    </div>
                )}
            </div>

            {/* Title Section */}
            <div className="venue-show-title relative flex justify-center items-center" style={{ minHeight: '1.2em' }}>
                <div className={`relative inline-block group-title-wrapper ${isEditingTitle ? 'invisible' : ''}`}>
                    <span>{show.title}</span>
                    <span className="pencil-spacer">
                        <span
                            role="button"
                            className="edit-icon-btn"
                            onPointerDown={(e) => e.stopPropagation()}
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsEditingTitle(true);
                            }}
                        >
                            <Edit2 size={10} className="edit-icon-svg" />
                        </span>
                    </span>
                </div>
                {isEditingTitle && (
                    <div className="absolute inset-0 flex items-center justify-center z-50">
                        <input
                            type="text"
                            className="glass-input"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={handleBlurTitle}
                            onKeyDown={handleKeyDownTitle}
                            onFocus={(e) => e.target.setSelectionRange(e.target.value.length, e.target.value.length)}
                            autoFocus
                            style={{
                                width: `calc(${editTitle.length}ch + 3rem)`,
                                minWidth: '100%',
                                textTransform: 'inherit',
                                lineHeight: 'inherit',
                                margin: 0,
                                height: 'auto',
                                boxSizing: 'border-box'
                            } as React.CSSProperties}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};
