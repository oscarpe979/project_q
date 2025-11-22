import React, { useState } from 'react';
import { User } from 'lucide-react';

interface MockLoginProps {
    onLogin: (user: { name: string; role: string }) => void;
}

export const MockLogin: React.FC<MockLoginProps> = ({ onLogin }) => {
    const [role, setRole] = useState('Stage Manager');

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        onLogin({ name: 'Demo User', role });
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-app)]">
            <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-[var(--border-light)]">
                <div className="flex flex-col items-center mb-8">
                    <div className="h-16 w-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white mb-4 shadow-lg shadow-blue-200">
                        <User size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--text-primary)]">Welcome Back</h1>
                    <p className="text-[var(--text-secondary)]">Sign in to VenueSched</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                            Select Role
                        </label>
                        <select
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            className="w-full p-3 rounded-lg border border-[var(--border-medium)] bg-[var(--bg-app)] focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        >
                            <option value="Stage Manager">Stage Manager</option>
                            <option value="Production Manager">Production Manager</option>
                            <option value="Cruise Director">Cruise Director</option>
                            <option value="Activities Manager">Activities Manager</option>
                        </select>
                    </div>

                    <button
                        type="submit"
                        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-md hover:shadow-lg transition-all transform active:scale-95"
                    >
                        Enter Demo Mode
                    </button>
                </form>

                <div className="mt-6 text-center text-xs text-[var(--text-tertiary)]">
                    MVP Build v0.1.0
                </div>
            </div>
        </div>
    );
};
