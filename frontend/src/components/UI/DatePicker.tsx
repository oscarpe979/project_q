import React from 'react';
import { DatePicker as MuiDatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface DatePickerProps {
    value: Date;
    onChange: (date: Date | null) => void;
    onClose: () => void;
}

export const DatePicker: React.FC<DatePickerProps> = ({ value, onChange, onClose }) => {
    return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <MuiDatePicker
                value={value}
                onChange={(newValue) => {
                    onChange(newValue);
                    onClose();
                }}
                open={true}
                onClose={onClose}
                slotProps={{
                    textField: {
                        // Hide the input field but keep it in the DOM for anchoring
                        style: {
                            width: 0,
                            height: 0,
                            padding: 0,
                            border: 'none',
                            visibility: 'hidden',
                            position: 'absolute'
                        }
                    },
                    popper: {
                        sx: {
                            // Ensure z-index is high enough
                            zIndex: 1300,
                        },
                        modifiers: [
                            {
                                name: 'offset',
                                options: {
                                    offset: [30, -50], // Move up by 8px
                                },
                            },
                        ],
                    },
                    desktopPaper: {
                        sx: {
                            // Glassy styles
                            backgroundColor: 'rgba(255, 255, 255, 0.85)',
                            backdropFilter: 'blur(12px)',
                            borderRadius: '16px',
                            border: '1px solid rgba(255, 255, 255, 0.5)',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                            // Override MUI default paper styles if needed
                            '& .MuiPickersCalendarHeader-root': {
                                // Custom header styles if needed
                            },
                            '& .MuiDayCalendar-weekDayLabel': {
                                fontWeight: 'bold',
                                color: '#6b7280'
                            },
                            '& .MuiPickersDay-root': {
                                width: '36px',
                                height: '36px',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 2px',
                                fontSize: '0.875rem',
                                lineHeight: 1,
                            },
                            '& .MuiPickersDay-root.Mui-selected': {
                                backgroundColor: '#3b82f6',
                                color: '#ffffff',
                                '&:hover': {
                                    backgroundColor: '#2563eb'
                                }
                            },
                            '& .MuiPickersDay-root.Mui-selected:focus': {
                                backgroundColor: '#3b82f6'
                            }
                        }
                    }
                }}
            />
        </LocalizationProvider>
    );
};
