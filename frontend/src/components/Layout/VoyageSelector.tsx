import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Calendar, Search } from 'lucide-react';
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
}

export const VoyageSelector: React.FC<VoyageSelectorProps> = ({ voyages, currentVoyageNumber, onSelect, title, status = 'draft' }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const filteredVoyages = voyages.filter(v =>
        v.voyage_number.toLowerCase().includes(searchTerm.toLowerCase())
    );

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
        <div className="voyage-selector" ref={dropdownRef} style={{ position: 'relative', zIndex: 50 }}>
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

            {isOpen && (
                <div className="voyage-dropdown" style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    left: 0,
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.99)',
                    backdropFilter: 'blur(16px)',
                    borderRadius: '16px',
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                    padding: '0.5rem',
                    overflow: 'hidden',
                    animation: 'fadeIn 0.2s ease-out'
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '0.5rem',
                        borderBottom: '1px solid rgba(0,0,0,0.05)',
                        marginBottom: '0.5rem'
                    }}>
                        <Search size={14} style={{ color: 'var(--text-tertiary)', marginRight: '0.5rem' }} />
                        <input
                            type="text"
                            placeholder="Search voyages..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{
                                border: 'none',
                                background: 'transparent',
                                width: '100%',
                                fontSize: '0.875rem',
                                outline: 'none',
                                color: 'var(--text-primary)'
                            }}
                            autoFocus
                        />
                    </div>

                    <div className="custom-scrollbar" style={{ maxHeight: '240px', overflowY: 'auto' }}>
                        {filteredVoyages.length > 0 ? (
                            filteredVoyages.map((voyage) => (
                                <button
                                    key={voyage.voyage_number}
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
                            ))
                        ) : (
                            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                                No voyages found
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
