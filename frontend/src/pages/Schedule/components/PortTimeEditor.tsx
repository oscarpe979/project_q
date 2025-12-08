import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { Clock } from 'lucide-react';
import { Backdrop } from '../../../components/UI/Backdrop';

interface PortTimeEditorProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (arrival: string | null, departure: string | null) => void;
    initialArrival: string | null;
    initialDeparture: string | null;
    portName: string;
    anchorEl: HTMLElement | null;
    onTabChange?: (tab: 'arrival' | 'departure') => void;
    activeTab?: 'arrival' | 'departure';
}

type Tab = 'arrival' | 'departure';
type Period = 'AM' | 'PM';

export const PortTimeEditor: React.FC<PortTimeEditorProps> = ({
    isOpen,
    onClose,
    onSave,
    initialArrival,
    initialDeparture,
    portName,
    anchorEl,
    onTabChange,
    activeTab: controlledActiveTab
}) => {
    const [internalActiveTab, setInternalActiveTab] = useState<Tab>('arrival');

    // Use controlled prop if available, otherwise internal state
    const activeTab = controlledActiveTab ?? internalActiveTab;

    // Parse initial time
    const parseTime = (timeStr: string | null) => {
        if (!timeStr || timeStr.trim().toLowerCase() === 'null') return { hour: '', minute: '', period: 'AM' as Period };
        // Handle "8:00 am" or "8:00" format
        const cleanStr = timeStr.toLowerCase().replace(/\s/g, '');
        const isPM = cleanStr.includes('pm');
        const [h, mPart] = cleanStr.replace(/[a-z]/g, '').split(':');

        let hour = parseInt(h);
        let minute = mPart;

        // If AM/PM was in the string, trust it. Otherwise infer from 24h time? 
        // Assuming input is usually 12h with am/pm or 24h.
        // Let's stick to the previous logic but clean the minute.

        let period: Period = 'AM';
        if (isPM) {
            period = 'PM';
        } else if (hour >= 12 && !cleanStr.includes('am')) {
            // Fallback for 24h time if no am/pm present
            period = 'PM';
            if (hour > 12) hour -= 12;
        } else if (hour === 0) {
            hour = 12;
        }

        return {
            hour: hour.toString().padStart(2, '0'),
            minute: minute,
            period
        };
    };

    // Initialize state only once when props change
    const [arrivalState, setArrivalState] = useState(() => parseTime(initialArrival));
    const [departureState, setDepartureState] = useState(() => parseTime(initialDeparture));

    // Update state if props change (e.g. reopening with different cell)
    useEffect(() => {
        setArrivalState(parseTime(initialArrival));
        setDepartureState(parseTime(initialDeparture));
    }, [initialArrival, initialDeparture, isOpen]);

    const popupRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (popupRef.current && !popupRef.current.contains(event.target as Node) &&
                anchorEl && !anchorEl.contains(event.target as Node)) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, onClose, anchorEl]);

    if (!isOpen || !anchorEl) return null;

    const handleSave = () => {
        const formatTime = (state: typeof arrivalState) => {
            if (!state.hour || !state.minute) return null;
            let h = parseInt(state.hour);
            if (state.period === 'PM' && h !== 12) h += 12;
            if (state.period === 'AM' && h === 12) h = 0;
            return `${h.toString().padStart(2, '0')}:${state.minute}`;
        };

        onSave(formatTime(arrivalState), formatTime(departureState));
        onClose();
    };

    // Update parent when tab changes
    const handleTabChange = (tab: Tab) => {
        setInternalActiveTab(tab);
        if (onTabChange) {
            onTabChange(tab);
        }
    };

    const currentState = activeTab === 'arrival' ? arrivalState : departureState;
    const setState = activeTab === 'arrival' ? setArrivalState : setDepartureState;

    const handleHourChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let val = e.target.value.replace(/\D/g, '');
        if (val.length > 2) val = val.slice(0, 2);
        if (parseInt(val) > 12) val = '12';
        if (val === '00') val = '12';
        setState(prev => ({ ...prev, hour: val }));
    };

    const handleMinuteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        let val = e.target.value.replace(/\D/g, '');
        if (val.length > 2) val = val.slice(0, 2);
        if (parseInt(val) > 59) val = '59';
        setState(prev => ({ ...prev, minute: val }));
    };

    const handleBlur = () => {
        setState(prev => ({
            ...prev,
            hour: prev.hour ? prev.hour.padStart(2, '0') : '',
            minute: prev.minute ? prev.minute.padStart(2, '0') : ''
        }));
    };

    // Calculate position
    const rect = anchorEl.getBoundingClientRect();
    const top = rect.bottom + window.scrollY + 8;
    const left = rect.left + window.scrollX + (rect.width / 2) - 160;

    const popupContent = (
        <div
            ref={popupRef}
            className="glass-time-editor-popup interactive-overlay"
            style={{
                position: 'absolute',
                top: `${top}px`,
                left: `${left}px`,
                zIndex: 1300,
            }}
            onClick={(e) => e.stopPropagation()}
        >
            {/* Header */}
            <div className="glass-time-header">
                <div className="glass-time-title-group">
                    <div className="glass-time-port-name">
                        {portName}
                    </div>
                    <div className="glass-time-subtitle">
                        Enter time
                    </div>
                </div>
                {/* Tabs */}
                <div className="glass-time-tabs">
                    <button
                        onClick={() => handleTabChange('arrival')}
                        className={`glass-time-tab-btn ${activeTab === 'arrival' ? 'active' : ''}`}
                    >
                        Arr
                    </button>
                    <button
                        onClick={() => handleTabChange('departure')}
                        className={`glass-time-tab-btn ${activeTab === 'departure' ? 'active' : ''}`}
                    >
                        Dep
                    </button>
                </div>
            </div>

            {/* Digital Input Area */}
            <div className="glass-time-inputs-container">
                {/* Hour Input */}
                <div className="glass-time-input-wrapper">
                    <input
                        type="text"
                        value={currentState.hour === '' ? '-' : currentState.hour}
                        onChange={handleHourChange}
                        onFocus={(e) => {
                            if (currentState.hour === '') e.target.select();
                        }}
                        onBlur={handleBlur}
                        placeholder="-"
                        className="glass-time-input"
                    />
                    <span className="glass-time-label">Hour</span>
                </div>

                <div className="glass-time-separator">:</div>

                {/* Minute Input */}
                <div className="glass-time-input-wrapper">
                    <input
                        type="text"
                        value={currentState.minute === '' ? '-' : currentState.minute}
                        onChange={handleMinuteChange}
                        onFocus={(e) => {
                            if (currentState.minute === '') e.target.select();
                        }}
                        onBlur={handleBlur}
                        placeholder="-"
                        className="glass-time-input"
                    />
                    <span className="glass-time-label">Minute</span>
                </div>

                {/* AM/PM Toggle */}
                <div className="glass-time-toggle-group ml-2">
                    <button
                        onClick={() => setState(prev => ({ ...prev, period: 'AM' }))}
                        className={`glass-time-toggle-btn ${currentState.period === 'AM' ? 'active' : ''}`}
                    >
                        AM
                    </button>
                    {/* Divider removed */}
                    <button
                        onClick={() => setState(prev => ({ ...prev, period: 'PM' }))}
                        className={`glass-time-toggle-btn ${currentState.period === 'PM' ? 'active' : ''}`}
                    >
                        PM
                    </button>
                </div>
            </div>

            {/* Actions */}
            <div className="glass-time-footer">
                <button
                    onClick={() => {
                        setState({ hour: '', minute: '', period: 'AM' });
                    }}
                    className="glass-time-icon-btn"
                    title="Clear time"
                >
                    <Clock size={20} />
                </button>
                <div className="flex gap-2">
                    <button
                        onClick={onClose}
                        className="glass-time-action-btn"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="glass-time-action-btn"
                    >
                        OK
                    </button>
                </div>
            </div>
        </div>
    );

    return ReactDOM.createPortal(
        <>
            {/* Blocking Backdrop for Grid Protection - Sibling to Popup */}
            <Backdrop onClose={onClose} zIndex={1299} />
            {popupContent}
        </>,
        document.body
    );
};
