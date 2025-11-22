import React from 'react';
import { Calendar, Settings, Upload, LogOut } from 'lucide-react';
import clsx from 'clsx';

interface MainLayoutProps {
    children: React.ReactNode;
    onImportClick?: () => void;
    user?: { name: string; role: string };
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, onImportClick, user }) => {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-[var(--bg-app)]">
            {/* Sidebar */}
            <aside className="w-64 glass-panel flex flex-col border-r border-[var(--border-light)] z-20">
                <div className="p-6 flex items-center gap-3">
                    <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                        RC
                    </div>
                    <span className="font-bold text-lg tracking-tight">VenueSched</span>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    <NavItem icon={<Calendar size={20} />} label="Schedule" active />
                    <NavItem icon={<Upload size={20} />} label="Import Grid" onClick={onImportClick} />
                    <NavItem icon={<Settings size={20} />} label="Settings" />
                </nav>

                <div className="p-4 border-t border-[var(--border-light)]">
                    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/50 transition-colors cursor-pointer">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs">
                            {user?.name.charAt(0) || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[var(--text-primary)] truncate">{user?.name || 'User'}</p>
                            <p className="text-xs text-[var(--text-secondary)] truncate">{user?.role || 'Staff'}</p>
                        </div>
                        <LogOut size={16} className="text-[var(--text-tertiary)]" />
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-w-0 relative">
                {/* Header */}
                <header className="h-16 glass-panel border-b border-[var(--border-light)] flex items-center justify-between px-6 z-10">
                    <div className="flex items-center gap-4">
                        <h1 className="text-xl font-semibold text-[var(--text-primary)]">Two70</h1>
                        <span className="px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium border border-green-200">
                            Live Mode
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="text-sm text-right">
                            <p className="font-medium">Production Manager</p>
                            <p className="text-xs text-[var(--text-secondary)]">Oasis of the Seas</p>
                        </div>
                        <div className="h-10 w-10 rounded-full bg-gray-200 border-2 border-white shadow-sm"></div>
                    </div>
                </header>

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-auto relative">
                    {children}
                </div>
            </main>
        </div>
    );
};

const NavItem = ({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) => {
    return (
        <button
            onClick={onClick}
            className={clsx(
                "flex items-center gap-3 w-full p-3 rounded-lg transition-all duration-200 text-sm font-medium",
                active
                    ? "bg-white shadow-sm text-[var(--text-accent)]"
                    : "text-[var(--text-secondary)] hover:bg-white/50 hover:text-[var(--text-primary)]"
            )}
        >
            {icon}
            <span>{label}</span>
        </button>
    );
};
