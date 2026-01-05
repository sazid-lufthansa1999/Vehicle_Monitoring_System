import React, { useState, useEffect } from 'react';
import { fetchViolations, getViolationVideoUrl } from '../api';
import { Play, Calendar, Hash, Tag, X, FileVideo } from 'lucide-react';

function ViolationArchive() {
    const [violations, setViolations] = useState([]);
    const [selectedVideo, setSelectedVideo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadArchive();
    }, []);

    const loadArchive = async () => {
        setLoading(true);
        try {
            const data = await fetchViolations();
            setViolations(data);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold">Historical Citations</h2>
                    <p className="text-gray-500 mt-1">Review and manage recorded behavior violations</p>
                </div>
                <button
                    onClick={loadArchive}
                    className="px-6 py-2.5 bg-accent/10 text-accent font-bold rounded-xl border border-accent/20 hover:bg-accent/20 transition-all flex items-center gap-2"
                >
                    🔄 Refresh Database
                </button>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map(i => <div key={i} className="h-64 bg-white/5 rounded-3xl animate-pulse" />)}
                </div>
            ) : violations.length === 0 ? (
                <div className="h-96 flex flex-col items-center justify-center text-gray-600 gap-4 glass rounded-[40px]">
                    <FileVideo size={64} className="opacity-20" />
                    <p className="font-medium tracking-wide">No violation records found in system</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {violations.map((v, i) => (
                        <div
                            key={i}
                            className="bg-navy/40 border border-white/5 rounded-3xl p-6 hover:border-accent/40 transition-all hover:translate-y-[-4px] group"
                        >
                            <div className="mb-4">
                                <span className="text-[10px] font-black tracking-widest text-danger bg-danger/10 px-3 py-1.5 rounded-lg uppercase">
                                    {v.type}
                                </span>
                            </div>

                            <div className="space-y-4 mb-6 text-sm">
                                <div className="flex items-center gap-3 text-gray-400">
                                    <Hash size={14} className="text-accent" />
                                    <span className="font-medium">ID: {v.id}</span>
                                </div>
                                <div className="flex items-center gap-3 text-gray-400">
                                    <Calendar size={14} className="text-accent" />
                                    <span className="font-medium">{v.time}</span>
                                </div>
                            </div>

                            <button
                                onClick={() => setSelectedVideo(v)}
                                className="w-full py-3 bg-white/5 hover:bg-accent hover:text-dark text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
                            >
                                <Play size={16} fill="currentColor" />
                                Review Evidence
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Video Modal */}
            {selectedVideo && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-8 bg-black/90 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="relative w-full max-w-5xl bg-navy rounded-[40px] border border-white/10 overflow-hidden shadow-2xl">
                        <button
                            onClick={() => setSelectedVideo(null)}
                            className="absolute top-8 right-8 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-10"
                        >
                            <X size={20} />
                        </button>
                        <div className="p-12">
                            <div className="mb-8">
                                <h3 className="text-2xl font-bold">{selectedVideo.type} Evidence</h3>
                                <p className="text-gray-500 uppercase text-xs font-bold tracking-widest mt-1">
                                    Vehicle ID {selectedVideo.id} — Recorded at {selectedVideo.time}
                                </p>
                            </div>
                            <video
                                controls
                                autoPlay
                                className="w-full rounded-2xl border border-white/5 shadow-2xl"
                                src={getViolationVideoUrl(selectedVideo.filename)}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ViolationArchive;
