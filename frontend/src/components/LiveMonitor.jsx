import React, { useMemo } from 'react';
import { getStreamUrl } from '../api';
import { Bell, ShieldAlert } from 'lucide-react';

function LiveMonitor({ stats }) {
    const streamUrl = useMemo(() => getStreamUrl(), []);
    return (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-full">
            {/* Video Stream */}
            <div className="lg:col-span-3 h-full min-h-[500px]">
                <div className="w-full h-full bg-black rounded-[32px] overflow-hidden border-2 border-white/5 shadow-2xl relative group">
                    <img
                        src={streamUrl}
                        alt="Live Monitor"
                        className="w-full h-full object-contain"
                    />
                    <div className="absolute top-6 left-6 flex gap-2">
                        <span className="px-4 py-2 bg-danger text-white text-[10px] font-black rounded-lg shadow-lg">LIVE</span>
                        <span className="px-4 py-2 bg-black/50 backdrop-blur-md text-white/70 text-[10px] font-bold rounded-lg border border-white/10 uppercase">
                            {stats.scene_type || "DETECTING..."} MODE
                        </span>
                        <span className="px-4 py-2 bg-black/50 backdrop-blur-md text-white/70 text-[10px] font-bold rounded-lg border border-white/10 uppercase">
                            Highway Cam 01
                        </span>
                    </div>
                    <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="px-6 py-2 bg-white text-dark text-xs font-bold rounded-full shadow-xl">
                            Expand View
                        </button>
                    </div>
                </div>
            </div>

            {/* Side Feed */}
            <div className="lg:col-span-1 flex flex-col gap-6">
                <div className="bg-navy/40 backdrop-blur-xl border border-white/5 rounded-[32px] p-6 flex-1 flex flex-col">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-2">
                            <Bell size={18} className="text-accent" />
                            <h3 className="font-bold">Real-time Activity</h3>
                        </div>
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Global</span>
                    </div>

                    <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                        {stats.recent_violations.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-3 grayscale opacity-30">
                                <ShieldAlert size={48} />
                                <p className="text-xs font-medium">Scanning for threats...</p>
                            </div>
                        ) : (
                            stats.recent_violations.slice().reverse().map((v, i) => (
                                <div
                                    key={i}
                                    className="p-4 rounded-2xl bg-white/5 border-l-4 border-danger hover:bg-white/10 transition-all group"
                                    style={{ animation: 'slideIn 0.3s ease-out' }}
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="text-xs font-black text-danger uppercase tracking-tighter">{v.type}</span>
                                        <span className="text-[10px] text-gray-500 font-mono">{v.timestamp.split('_')[1]}</span>
                                    </div>
                                    <p className="text-sm font-bold text-gray-200">Vehicle ID: {v.tracker_id}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LiveMonitor;
