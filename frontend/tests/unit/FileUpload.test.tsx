import { render, screen, fireEvent } from '@testing-library/react';
import { FileDropZone } from '../../src/components/Uploader/FileDropZone';
import { vi } from 'vitest';

describe('FileDropZone', () => {
    it('renders drop zone with label', () => {
        render(<FileDropZone onFileSelect={vi.fn()} />);
        expect(screen.getByText(/Drop CD Grid or AM Grid here/i)).toBeInTheDocument();
    });

    it('calls onFileSelect when file is selected', () => {
        const onFileSelect = vi.fn();
        render(<FileDropZone onFileSelect={onFileSelect} />);

        const file = new File(['dummy content'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const input = screen.getByLabelText(/Drop CD Grid or AM Grid here/i);

        // The input is hidden but we can trigger change on it
        fireEvent.change(input, { target: { files: [file] } });

        expect(onFileSelect).toHaveBeenCalledWith(file);
    });
});
