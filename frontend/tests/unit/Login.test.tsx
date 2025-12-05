import { render, screen } from '@testing-library/react';
import { LoginPage } from '../../src/pages/Login/LoginPage';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

// Mock useNavigate
const mockedUsedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
        ...actual,
        useNavigate: () => mockedUsedNavigate,
    };
});

describe('LoginPage', () => {
    it('renders login form correctly', () => {
        render(
            <BrowserRouter>
                <LoginPage onLogin={vi.fn()} />
            </BrowserRouter>
        );

        expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });
});
