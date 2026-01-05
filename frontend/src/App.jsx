import React, { useState, useEffect } from 'react';
import {
  Activity,
  LayoutDashboard,
  FolderLock,
  Settings,
  LogOut,
  Menu,
  X,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { fetchStats, getStreamUrl, setAuthToken } from './api';
import { auth } from './firebase/config';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import LiveMonitor from './components/LiveMonitor';
import ViolationArchive from './components/ViolationArchive';
import CamSettings from './components/CamSettings';
import Login from './components/Login';

function App() {
  const [user, setUser] = useState(null);
  const [role, setRole] = useState('operator'); // 'admin' or 'operator'
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('live');
  const [stats, setStats] = useState({ in_count: 0, out_count: 0, total_violations: 0, recent_violations: [] });
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      if (currentUser) {
        const token = await currentUser.getIdToken();
        setAuthToken(token);
        setUser(currentUser);
        // Determine role (Simple simulation based on email)
        const userRole = currentUser.email?.toLowerCase().includes('admin') ? 'admin' : 'operator';
        setRole(userRole);
      } else {
        setAuthToken(null);
        setUser(null);
        setRole('operator');
      }
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!user) return;
    const interval = setInterval(async () => {
      try {
        const data = await fetchStats();
        setStats(data);
      } catch (e) {
        console.error("Failed to fetch stats", e);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = () => {
    signOut(auth);
  };

  const navItems = [
    { id: 'live', label: 'Live Monitor', icon: LayoutDashboard, roles: ['admin', 'operator'] },
    { id: 'archive', label: 'Violation Archive', icon: FolderLock, roles: ['admin', 'operator'] },
    { id: 'settings', label: 'Cam Settings', icon: Settings, roles: ['admin'] },
  ];

  const filteredNav = navItems.filter(item => item.roles.includes(role));

  if (loading) {
    return (
      <div className="h-screen w-full bg-dark flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="flex h-screen bg-dark text-white overflow-hidden">
      {/* Sidebar */}
      <aside className={`bg-navy border-r border-white/10 transition-all duration-300 ${isSidebarOpen ? 'w-64' : 'w-20'} flex flex-col`}>
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg shadow-accent/20">
            <Activity className="text-dark w-6 h-6" />
          </div>
          {isSidebarOpen && <span className="font-bold text-xl tracking-tight">AI Vision</span>}
        </div>

        <nav className="flex-1 px-4 py-6">
          {filteredNav.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-4 p-4 rounded-xl transition-all mb-2 ${activeTab === item.id
                ? 'bg-accent/10 text-accent'
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`}
            >
              <item.icon size={22} />
              {isSidebarOpen && <span className="font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="bg-white/5 rounded-2xl p-4 flex items-center justify-between">
            {isSidebarOpen && (
              <div className="flex flex-col">
                <span className="text-sm font-semibold truncate max-w-[120px]">{user?.email?.split('@')[0]}</span>
                <span className={`text-[10px] uppercase tracking-widest font-bold ${role === 'admin' ? 'text-accent' : 'text-gray-500'}`}>
                  {role}
                </span>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-danger/20 rounded-lg text-gray-400 hover:text-danger transition-colors"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-20 border-b border-white/5 bg-navy/50 backdrop-blur-xl px-8 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold capitalize">{activeTab.replace('-', ' ')}</h2>
            <div className="flex items-center gap-2 px-3 py-1 bg-success/10 text-success rounded-full text-xs font-bold border border-success/20">
              <div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
              LIVE FEED
            </div>
          </div>

          <div className="flex gap-6">
            <StatSmall label="IN" value={stats.in_count} icon={ArrowDownRight} color="text-accent" />
            <StatSmall label="OUT" value={stats.out_count} icon={ArrowUpRight} color="text-accent" />
            <StatSmall label="VIOLATIONS" value={stats.total_violations} icon={AlertTriangle} color="text-danger" alert />
          </div>
        </header>

        {/* View Area */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'live' && <LiveMonitor stats={stats} />}
          {activeTab === 'archive' && <ViolationArchive />}
          {activeTab === 'settings' && <CamSettings />}
        </div>
      </main>
    </div>
  );
}

function StatSmall({ label, value, icon: Icon, color, alert }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 border border-white/5 ${alert ? 'animate-pulse border-danger/20' : ''}`}>
      <div className={`p-1.5 rounded-lg bg-white/5 ${color}`}>
        <Icon size={14} />
      </div>
      <div className="flex flex-col">
        <span className="text-[10px] text-gray-500 font-bold tracking-wider">{label}</span>
        <span className={`text-sm font-bold ${color}`}>{value}</span>
      </div>
    </div>
  );
}

export default App;
