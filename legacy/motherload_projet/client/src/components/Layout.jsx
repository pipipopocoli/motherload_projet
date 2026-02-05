import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Library, ScanLine, Calendar, GraduationCap, Settings, Menu } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { useState } from 'react';

const SidebarItem = ({ icon: Icon, label, to, active }) => {
    return (
        <Link to={to}>
            <div className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative",
                active ? "bg-white/10 text-white shadow-lg" : "text-slate-400 hover:text-white hover:bg-white/5"
            )}>
                {active && (
                    <motion.div
                        layoutId="activeTab"
                        className="absolute left-0 w-1 h-6 bg-pink-500 rounded-r-full"
                    />
                )}
                <Icon size={20} className={clsx("transition-colors", active ? "text-pink-400" : "group-hover:text-pink-300")} />
                <span className="font-medium text-sm">{label}</span>
            </div>
        </Link>
    );
};

const Layout = ({ children }) => {
    const location = useLocation();
    const [collapsed, setCollapsed] = useState(false);

    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', to: '/' },
        { icon: Library, label: 'Library', to: '/library' },
        { icon: ScanLine, label: 'Scanner', to: '/scanner' },
        { icon: Calendar, label: 'Calendar', to: '/calendar' },
        { icon: GraduationCap, label: 'Bourses', to: '/scholarships' },
    ];

    return (
        <div className="flex h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: collapsed ? 80 : 260 }}
                className="h-full bg-slate-900/50 backdrop-blur-xl border-r border-white/5 flex flex-col relative z-20"
            >
                <div className="p-6 flex items-center justify-between">
                    {!collapsed && (
                        <motion.h1
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="font-bold text-xl tracking-tighter"
                        >
                            Grand <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400">Librarium</span>
                        </motion.h1>
                    )}
                    <button onClick={() => setCollapsed(!collapsed)} className="p-2 hover:bg-white/5 rounded-lg text-slate-400">
                        <Menu size={18} />
                    </button>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.to}
                            icon={item.icon}
                            label={collapsed ? '' : item.label}
                            to={item.to}
                            active={location.pathname === item.to}
                        />
                    ))}
                </nav>

                <div className="p-4 border-t border-white/5">
                    <SidebarItem icon={Settings} label={collapsed ? '' : 'Settings'} to="/settings" active={location.pathname === '/settings'} />
                </div>
            </motion.aside>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden relative">
                {/* Background Gradients */}
                <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-violet-600/20 rounded-full blur-[120px] pointer-events-none" />
                <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-pink-600/10 rounded-full blur-[120px] pointer-events-none" />

                <div className="h-full overflow-y-auto p-8 custom-scrollbar relative z-10">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
