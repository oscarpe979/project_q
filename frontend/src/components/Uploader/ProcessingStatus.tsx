
import React, { useEffect, useState } from 'react';
import { Check, Loader2, Clock, CheckCircle } from 'lucide-react';
import clsx from 'clsx';

interface ProcessingStatusProps {
    startTime?: number;
    isSuccess?: boolean;
    onViewSchedule?: () => void;
}

const STEPS = [
    { id: 1, label: 'Encrypting data for secure processing...', duration: 2000 },
    { id: 2, label: 'Gemini AI analyzing schedule structure...', duration: 35000 },
    { id: 3, label: 'Extracting events and itinerary...', duration: 15000 },
    { id: 4, label: 'Formatting data for grid view...', duration: 3000 },
];

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ startTime: propStartTime, isSuccess = false, onViewSchedule }) => {
    // Use state for startTime to prevent resets on re-renders, default to prop or now
    const [startTime] = useState(() => propStartTime || Date.now());
    const [elapsed, setElapsed] = useState(0);
    const [currentStep, setCurrentStep] = useState(1);

    // Timer logic
    useEffect(() => {
        if (isSuccess) return; // Stop timer on success

        // Update immediately
        setElapsed(Math.floor((Date.now() - startTime) / 1000));

        const timer = setInterval(() => {
            setElapsed(Math.floor((Date.now() - startTime) / 1000));
        }, 1000);

        return () => clearInterval(timer);
    }, [startTime, isSuccess]);

    // Step progression logic
    useEffect(() => {
        let timeout: ReturnType<typeof setTimeout>;

        const processStep = (stepIndex: number) => {
            // If we've gone past the last step, stop
            if (stepIndex >= STEPS.length) return;

            // Determine duration based on success state
            // If success, fast forward (3000ms). If not, use step duration.
            const duration = isSuccess ? 3000 : STEPS[stepIndex].duration;

            // If we are at the last step AND not successful yet, WAIT.
            // The last step is "Formatting data...", we want to keep showing this until isSuccess becomes true.
            if (!isSuccess && stepIndex === STEPS.length - 1) {
                return;
            }

            timeout = setTimeout(() => {
                setCurrentStep(stepIndex + 2); // Move to next step (1-based + 1)
                processStep(stepIndex + 1);
            }, duration);
        };

        // If we are already past the current step (e.g. re-render), we need to continue from where we are
        // But for simplicity in this "fast forward" logic, we can just trigger the next step from currentStep
        // The stepIndex is 0-based, currentStep is 1-based.
        // So if currentStep is 1, we are processing stepIndex 0.
        processStep(currentStep - 1);

        return () => clearTimeout(timeout);
    }, [isSuccess, currentStep]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // Only show success UI when ALL steps are visually complete AND isSuccess is true
    const showSuccessUI = isSuccess && currentStep > STEPS.length;

    if (showSuccessUI) {
        return (
            <div className="processing-status-container success">
                <div className="success-icon-wrapper">
                    <CheckCircle size={64} className="success-icon" />
                </div>
                <h3 className="success-title">Schedule Generated Successfully!</h3>
                <p className="success-message">
                    Your grid has been processed and is ready for review.
                </p>
                <div className="success-stats">
                    <div className="stat-item">
                        <Clock size={16} />
                        <span>Processed in {formatTime(elapsed)}</span>
                    </div>
                </div>
                <button onClick={onViewSchedule} className="view-schedule-btn">
                    View Schedule
                </button>
            </div>
        );
    }

    return (
        <div className="processing-status-container">
            {/* Throbber / Pulse Effect */}
            <div className="processing-icon-wrapper">
                <div className="processing-pulse"></div>
                <Loader2 className="processing-spinner" size={32} />
            </div>

            <div className="processing-header">
                <h3>AI Processing in Progress</h3>
                <p className="processing-hint">This usually takes about a minute</p>
                <div className="processing-timer">
                    <Clock size={14} />
                    <span>{formatTime(elapsed)}</span>
                </div>
            </div>

            <div className="processing-steps">
                {STEPS.map((step) => {
                    const isComplete = currentStep > step.id;
                    const isCurrent = currentStep === step.id;

                    return (
                        <div
                            key={step.id}
                            className={clsx(
                                "processing-step",
                                isComplete && "completed",
                                isCurrent && "current"
                            )}
                        >
                            <div className="step-icon">
                                {isComplete ? (
                                    <Check size={14} strokeWidth={3} />
                                ) : (
                                    <div className="step-dot" />
                                )}
                            </div>
                            <span className="step-label">{step.label}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
