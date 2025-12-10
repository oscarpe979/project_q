import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Calendar, Search, RotateCcw, RotateCw, X } from 'lucide-react';
import { Virtuoso } from 'react-virtuoso';
import clsx from 'clsx';

interface Voyage {
    voyage_number: string;
    start_date: string;
    end_date: string;
}

interface VoyageSelectorProps {
    voyages: Voyage[];
    currentVoyageNumber: string;
    onSelect: (voyageNumber: string) => void;
    title: string;
    status?: 'live' | 'draft' | 'modified';
    undo?: () => void;
    redo?: () => void;
    canUndo?: boolean;
    canRedo?: boolean;
    onNewSchedule?: () => void;
    isNewDraft?: boolean;
    onSearch?: (term: string) => void;
    onLoadMore?: () => void;
    isLoadingMore?: boolean;
    hasMore?: boolean;
}

export const VoyageSelector: React.FC<VoyageSelectorProps> = ({
    voyages,
    currentVoyageNumber,
    onSelect,
    title,
    status = 'draft',
    undo: onUndo,
    redo: onRedo,
    canUndo = false,
    canRedo = false,
    onNewSchedule,
    isNewDraft,
    onSearch,
    onLoadMore,
    isLoadingMore = false,
    hasMore = false
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);
    const [dropdownHeight, setDropdownHeight] = useState(550);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const resizeRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleResize);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        const handleResize = (e: MouseEvent) => {
            if (resizeRef.current && dropdownRef.current) {
                const rect = dropdownRef.current.querySelector('.voyage-dropdown')?.getBoundingClientRect();
                if (rect) {
                    const newHeight = e.clientY - rect.top;
                    setDropdownHeight(Math.max(200, Math.min(newHeight, 600))); // Min 200px, Max 600px
                }
            }
        };

        const handleMouseDownResize = (e: React.MouseEvent) => {
            e.preventDefault();
            document.addEventListener('mousemove', handleResize);
            document.addEventListener('mouseup', handleMouseUp);
        };

        // Attach resize handler to ref for use in render
        (resizeRef.current as any) = handleMouseDownResize;

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('mousemove', handleResize);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);

    // Reset expanded state when closed
    useEffect(() => {
        if (!isOpen) {
            setIsExpanded(false);
        }
    }, [isOpen]);

    // Use ref to access latest onSearch without triggering effect re-runs
    const onSearchRef = useRef(onSearch);
    useEffect(() => {
        onSearchRef.current = onSearch;
    }, [onSearch]);

    // Debounced Search
    useEffect(() => {
        const timer = setTimeout(() => {
            if (onSearchRef.current) {
                onSearchRef.current(searchTerm);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchTerm]); // Only trigger when searchTerm changes

    // Filter logic if needed (handled by backend if onSearch is present)
    const filteredVoyages = onSearch ? voyages : voyages.filter(v =>
        v.voyage_number.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Visible Logic: Show everything if expanded or searching. Show 5 if collapsed.
    // If searching (backend mode), we generally want to show results as they come for better UX,
    // but preserving "initial 5" rule for consistency is fine.
    const visibleVoyages = isExpanded ? filteredVoyages : filteredVoyages.slice(0, 5);

    // Show "View More" if we have more local items hidden OR if backend has more pages
    // AND we are not currently loading
    const showLoadMore = !isLoadingMore && !isExpanded && (filteredVoyages.length > 5 || hasMore);

    const observerTarget = useRef<any>(null);

    const lastLoadCallRef = useRef(0);

    // Intersection Observer for Infinite Scroll
    useEffect(() => {
        // Only attach observer if we are expanded.
        // If not expanded, the "View More" button acts as a manual trigger to expand.
        if (!isExpanded) return;

        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    const now = Date.now();
                    // Throttle: Only call load more once every 1s to prevent loops
                    if (now - lastLoadCallRef.current < 1000) return;

                    // Trigger load more if backend has more
                    if (onLoadMore && !isLoadingMore && hasMore) {
                        lastLoadCallRef.current = now;
                        onLoadMore();
                    }
                }
            },
            { threshold: 0.1, rootMargin: '100px' }
        );

        if (observerTarget.current) {
            observer.observe(observerTarget.current);
        }

        return () => observer.disconnect();
    }, [isExpanded, onLoadMore, isLoadingMore, hasMore]);

    const getStatusText = () => {
        switch (status) {
            case 'live': return 'Live';
            case 'modified': return 'Modified';
            case 'draft': return 'New Draft';
            default: return 'Draft';
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case 'live': return '#10b981'; // Green
            case 'modified': return '#f59e0b'; // Amber
            case 'draft': return '#6366f1'; // Indigo
            default: return '#9ca3af';
        }
    };

    return (
        <div className="voyage-selector" ref={dropdownRef} style={{ position: 'relative', zIndex: 50, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
                className={clsx(
                    "voyage-selector-btn",
                    isOpen && "active"
                )}
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.5rem 1rem',
                    background: 'rgba(255, 255, 255, 0.83)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(216, 212, 212, 0.54)',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    minWidth: '250px',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    textAlign: 'left'
                }}
            >
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '25px',
                    height: '25px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                    color: 'white',
                    boxShadow: '0 2px 4px rgba(99, 102, 241, 0.3)'
                }}>
                    <Calendar size={14} strokeWidth={2.5} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', flex: 1, gap: '2px' }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.95rem', fontWeight: 700, lineHeight: 1.2, color: 'var(--text-primary)' }}>
                            {title} -
                        </span>
                        <span style={{
                            fontSize: '0.90rem',
                            color: currentVoyageNumber ? 'var(--text-secondary)' : 'var(--text-tertiary)',
                            fontWeight: 500,
                            fontStyle: currentVoyageNumber ? 'normal' : 'italic'
                        }}>
                            {currentVoyageNumber ? `VY ${currentVoyageNumber}` : 'New Draft'}
                        </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <span className="status-dot" style={{ backgroundColor: getStatusColor(), width: '6px', height: '6px' }}></span>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {getStatusText()}
                        </span>
                    </div>
                </div>

                <ChevronDown
                    size={16}
                    style={{
                        color: 'var(--text-tertiary)',
                        transform: isOpen ? 'rotate(180deg)' : 'none',
                        transition: 'transform 0.2s ease',
                        marginLeft: '0.5rem'
                    }}
                />
            </button>

            <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button
                    onClick={onUndo}
                    disabled={!canUndo}
                    title="Undo (Ctrl+Z)"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        border: '1px solid rgba(216, 212, 212, 0.54)',
                        background: 'rgba(255, 255, 255, 0.83)',
                        backdropFilter: 'blur(12px)',
                        cursor: canUndo ? 'pointer' : 'not-allowed',
                        color: canUndo ? 'var(--text-primary)' : 'var(--text-tertiary)',
                        opacity: canUndo ? 1 : 0.5,
                        transition: 'all 0.2s ease',
                        boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.03)'
                    }}
                    onMouseEnter={(e) => { if (canUndo) e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.05)' }}
                    onMouseLeave={(e) => { if (canUndo) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.83)' }}
                >
                    <RotateCcw size={14} />
                </button>
                <button
                    onClick={onRedo}
                    disabled={!canRedo}
                    title="Redo (Ctrl+Y)"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        border: '1px solid rgba(216, 212, 212, 0.54)',
                        background: 'rgba(255, 255, 255, 0.83)',
                        backdropFilter: 'blur(12px)',
                        cursor: canRedo ? 'pointer' : 'not-allowed',
                        color: canRedo ? 'var(--text-primary)' : 'var(--text-tertiary)',
                        opacity: canRedo ? 1 : 0.5,
                        transition: 'all 0.2s ease',
                        boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.03)'
                    }}
                    onMouseEnter={(e) => { if (canRedo) e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.05)' }}
                    onMouseLeave={(e) => { if (canRedo) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.83)' }}
                >
                    <RotateCw size={14} />
                </button>
            </div>

            {isOpen && (
                <div className="voyage-dropdown interactive-overlay" style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    left: 0,
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.99)',
                    backdropFilter: 'blur(8px)',
                    borderRadius: '16px',
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                    padding: '0.5rem', // Add bottom padding to prevent scrollbar hitting edge
                    overflow: 'hidden',
                    animation: 'fadeIn 0.15s ease-out',
                    display: 'flex',
                    flexDirection: 'column',
                    maxHeight: isExpanded ? 'none' : '650px', // Comfortably fit 5 items + view more
                    height: isExpanded ? `${dropdownHeight}px` : '450px', // Explicit height for Virtuoso
                }}>
                    <div style={{
                        padding: '0.75rem',
                        borderBottom: '1px solid rgba(0,0,0,0.05)',
                        flexShrink: 0
                    }}>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            width: '100%',
                            background: '#fff',
                            border: '1px solid rgba(0,0,0,0.1)',
                            borderRadius: '24px',
                            padding: '0.5rem 1rem',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.06)',
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.06)';
                                e.currentTarget.style.borderColor = 'rgba(0,0,0,0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.06)';
                                e.currentTarget.style.borderColor = 'rgba(0,0,0,0.1)';
                            }}
                        >
                            <Search size={16} style={{ color: '#9aa0a6', marginRight: '0.75rem' }} />
                            <input
                                type="text"
                                placeholder={onSearch ? "Deep search voyages..." : "Search voyages..."}
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{
                                    border: 'none',
                                    background: 'transparent',
                                    width: '100%',
                                    fontSize: '1rem', // Google uses slightly larger text
                                    outline: 'none',
                                    color: '#202124', // Google dark grey
                                    height: '24px'
                                }}
                                autoFocus
                            />
                            {searchTerm && (
                                <button
                                    onClick={() => setSearchTerm('')}
                                    aria-label="Clear search"
                                    style={{
                                        border: 'none',
                                        background: 'transparent',
                                        padding: '4px',
                                        cursor: 'pointer',
                                        color: '#70757a',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        borderRadius: '50%',
                                        marginLeft: '0.25rem'
                                    }}
                                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f1f3f4'}
                                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                >
                                    <X size={18} />
                                </button>
                            )}
                        </div>
                    </div>

                    <div style={{ padding: '0.5rem', borderBottom: '1px solid rgba(0,0,0,0.05)', flexShrink: 0 }}>
                        <button
                            onClick={() => {
                                if (!isNewDraft && onNewSchedule) {
                                    onNewSchedule();
                                    setIsOpen(false);
                                }
                            }}
                            disabled={isNewDraft}
                            style={{
                                width: '100%',
                                textAlign: 'left',
                                padding: '0.75rem',
                                borderRadius: '8px',
                                border: isNewDraft ? '1px dashed #e5e7eb' : '1px dashed #6366f1',
                                background: isNewDraft ? 'rgba(0,0,0,0.02)' : 'rgba(99, 102, 241, 0.05)',
                                cursor: isNewDraft ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                color: isNewDraft ? '#9ca3af' : '#6366f1',
                                fontWeight: 600,
                                fontSize: '0.9rem',
                                transition: 'all 0.2s',
                                opacity: isNewDraft ? 0.6 : 1
                            }}
                            onMouseEnter={(e) => !isNewDraft && (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)')}
                            onMouseLeave={(e) => !isNewDraft && (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.05)')}
                        >
                            <Calendar size={16} />
                            <span>New Schedule</span>
                        </button>
                    </div>

                    <div
                        className="custom-scrollbar"
                        style={{ flex: 1, height: '100%', overflowY: isExpanded ? 'hidden' : 'auto' }}
                    >
                        {visibleVoyages.length > 0 ? (
                            <Virtuoso
                                className="custom-scrollbar"
                                style={{ height: '100%' }}
                                data={visibleVoyages}
                                endReached={() => {
                                    if (isExpanded && hasMore && !isLoadingMore && onLoadMore) {
                                        onLoadMore();
                                    }
                                }}
                                itemContent={(index, voyage) => {
                                    const currentDate = new Date(voyage.start_date);
                                    const currentMonthYear = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

                                    let showHeader = false;
                                    if (index === 0) {
                                        showHeader = true;
                                    } else {
                                        const prevDate = new Date(visibleVoyages[index - 1].start_date);
                                        const prevMonthYear = prevDate.toLocaleString('default', { month: 'long', year: 'numeric' });
                                        if (currentMonthYear !== prevMonthYear) {
                                            showHeader = true;
                                        }
                                    }

                                    return (
                                        <div style={{ paddingBottom: '2px' }}>
                                            {showHeader && (
                                                <div style={{
                                                    padding: '0.75rem 1rem 0.25rem 1rem',
                                                    fontSize: '0.75rem',
                                                    fontWeight: 700,
                                                    color: 'var(--text-tertiary)',
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '0.05em',
                                                    marginTop: index > 0 ? '0.5rem' : '0',
                                                    borderTop: index > 0 ? '1px solid rgba(0,0,0,0.06)' : 'none',
                                                    display: 'flex',
                                                    alignItems: 'center'
                                                }}>
                                                    {currentMonthYear}
                                                </div>
                                            )}
                                            <button
                                                onClick={() => {
                                                    onSelect(voyage.voyage_number);
                                                    setIsOpen(false);
                                                }}
                                                style={{
                                                    width: '100%',
                                                    textAlign: 'left',
                                                    padding: '0.75rem',
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    background: voyage.voyage_number === currentVoyageNumber ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    gap: '2px',
                                                    transition: 'background 0.2s'
                                                }}
                                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = voyage.voyage_number === currentVoyageNumber ? 'rgba(99, 102, 241, 0.15)' : 'rgba(0,0,0,0.03)'}
                                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = voyage.voyage_number === currentVoyageNumber ? 'rgba(99, 102, 241, 0.1)' : 'transparent'}
                                            >
                                                <span style={{
                                                    fontSize: '0.9rem',
                                                    fontWeight: 600,
                                                    color: voyage.voyage_number === currentVoyageNumber ? '#6366f1' : 'var(--text-primary)'
                                                }}>
                                                    VY {voyage.voyage_number}
                                                </span>
                                                <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                                    {voyage.start_date}
                                                </span>
                                            </button>
                                        </div>
                                    );
                                }}
                                components={{
                                    Footer: () => (
                                        <div style={{ padding: '0.1rem 0.5rem 0.5rem 0.5rem' }}>
                                            {/* Show "View More" button in collapsed state */}
                                            {showLoadMore && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setIsExpanded(true);
                                                    }}
                                                    style={{
                                                        width: '100%',
                                                        padding: '0.7rem',
                                                        marginTop: '0',
                                                        border: 'none',
                                                        background: 'transparent',
                                                        color: '#4f46e5',
                                                        fontSize: '0.85rem',
                                                        fontWeight: 700,
                                                        cursor: 'pointer',
                                                        borderRadius: '8px',
                                                        transition: 'all 0.2s ease',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        gap: '0.5rem',
                                                    }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.color = '#3730a3';
                                                        e.currentTarget.style.background = 'rgba(99, 102, 241, 0.05)';
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.color = '#4f46e5';
                                                        e.currentTarget.style.background = 'transparent';
                                                    }}
                                                >
                                                    <ChevronDown size={14} />
                                                    View More
                                                </button>
                                            )}

                                            {/* Show manual Load More or Loading in expanded state */}
                                            {isExpanded && hasMore && !isLoadingMore && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (onLoadMore) onLoadMore();
                                                    }}
                                                    style={{
                                                        width: '100%',
                                                        padding: '0.75rem',
                                                        background: 'rgba(99, 102, 241, 0.05)',
                                                        color: '#6366f1',
                                                        border: 'none',
                                                        borderRadius: '8px',
                                                        fontSize: '0.85rem',
                                                        fontWeight: 600,
                                                        cursor: 'pointer',
                                                        marginBottom: '0.5rem'
                                                    }}
                                                >
                                                    Load More Voyages
                                                </button>
                                            )}
                                            {isLoadingMore && (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', opacity: 0.5 }}>
                                                    {[1, 2].map(i => (
                                                        <div key={i} style={{
                                                            height: '50px',
                                                            borderRadius: '8px',
                                                            background: 'linear-gradient(90deg, #f0f0f0 0%, #f8f8f8 50%, #f0f0f0 100%)',
                                                            backgroundSize: '200% 100%',
                                                            animation: 'shimmer 1.5s infinite'
                                                        }}></div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )
                                }}
                            />
                        ) : (
                            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                                {isLoadingMore ? 'Loading...' : 'No voyages found'}
                            </div>
                        )}
                    </div>

                    {/* Styles remain same */}
                    <style>{`
                        @keyframes shimmer {
                            0% { background-position: 200% 0; }
                            100% { background-position: -200% 0; }
                        }
                        /* Scrollbar styles still apply if needed, but Virtuoso manages scrolling */
                    `}</style>

                    {/* Resize Handle */}
                    {isExpanded && (
                        <div
                            onMouseDown={(e) => (resizeRef.current as any)(e)}
                            style={{
                                height: '16px',
                                cursor: 'ns-resize',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0,
                                marginTop: 'auto',
                                paddingTop: '8px',
                                paddingBottom: '2px',
                                background: '#fff', // Ensure handle has background over list
                                zIndex: 10
                            }}
                        >
                            <div style={{
                                width: '40px',
                                height: '4px',
                                borderRadius: '2px',
                                background: 'rgba(0,0,0,0.2)',
                                transition: 'background 0.2s'
                            }}
                                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.3)'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.2)'}
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
