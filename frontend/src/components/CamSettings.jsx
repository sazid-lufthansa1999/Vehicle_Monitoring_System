import React, { useState, useRef } from 'react';
import { switchCamera, uploadMedia } from '../api';
import { Camera, CloudUpload, CheckCircle, Smartphone, Monitor } from 'lucide-react';

function CamSettings() {
    const [uploadStatus, setUploadStatus] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef(null);

    const presets = [
        { name: 'Source 1 (Main Road)', source: 'road_monitoring.mp4', icon: Monitor },
        { name: 'Source 2 (Parking)', source: 'parking2.mp4', icon: Smartphone },
        { name: 'Source 3 (4K Highway)', source: '2103099-uhd_3840_2160_30fps.mp4', icon: Camera },
    ];

    const handleSwitch = async (source) => {
        try {
            await switchCamera(source);
            alert(`Switched to ${source}. Stream will restart shortly.`);
            window.location.reload();
        } catch (e) {
            alert("Failed to switch camera.");
        }
    };

    const handleButtonClick = () => {
        fileInputRef.current?.click();
    };

    const onFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setIsUploading(true);
        setUploadStatus('Uploading to secure server...');
        try {
            await uploadMedia(file);
            setUploadStatus('Finalizing AI initialization...');
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (e) {
            setUploadStatus('Error during upload.');
            setIsUploading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
                <h2 className="text-3xl font-bold">Cam Configuration</h2>
                <p className="text-gray-500 mt-1">Manage input sources and analyze custom media</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Upload Card */}
                <div className="bg-navy/40 border-2 border-dashed border-white/10 rounded-[40px] p-10 flex flex-col items-center justify-center text-center group hover:border-accent/40 transition-all relative overflow-hidden">
                    <div className="absolute inset-0 bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="w-20 h-20 bg-accent/10 rounded-3xl flex items-center justify-center mb-6 text-accent">
                        {isUploading ? <CloudUpload className="animate-bounce" size={40} /> : <CloudUpload size={40} />}
                    </div>
                    <h3 className="text-xl font-bold mb-2">Custom Media Analysis</h3>
                    <p className="text-gray-400 text-sm max-w-xs mb-8">
                        Upload your own video or image file to analyze behavior and traffic patterns.
                    </p>

                    <div className="relative z-10">
                        <input
                            type="file"
                            className="hidden"
                            onChange={onFileUpload}
                            accept="video/*,image/*"
                            ref={fileInputRef}
                        />
                        <button
                            onClick={handleButtonClick}
                            disabled={isUploading}
                            className="px-8 py-3 bg-accent text-dark font-black rounded-xl shadow-lg shadow-accent/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                        >
                            {isUploading ? 'PLEASE WAIT...' : 'SELECT FILE'}
                        </button>
                    </div>

                    {uploadStatus && (
                        <div className="mt-6 flex items-center gap-2 text-accent font-bold text-xs uppercase tracking-widest">
                            <CheckCircle size={14} className="animate-pulse" />
                            {uploadStatus}
                        </div>
                    )}
                </div>

                {/* Presets Card */}
                <div className="bg-navy/40 border border-white/5 rounded-[40px] p-10">
                    <h3 className="text-xl font-bold mb-8">Network Presets</h3>
                    <div className="space-y-4">
                        {presets.map((cam, idx) => (
                            <button
                                key={idx}
                                onClick={() => handleSwitch(cam.source)}
                                className="w-full p-6 bg-white/5 border border-white/5 rounded-3xl hover:border-accent/40 hover:bg-white/10 transition-all flex items-center justify-between group"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-white/5 rounded-2xl text-gray-400 group-hover:text-accent transition-colors">
                                        <cam.icon size={20} />
                                    </div>
                                    <span className="font-bold text-gray-300">{cam.name}</span>
                                </div>
                                <div className="w-1.5 h-1.5 bg-accent rounded-full group-hover:animate-ping" />
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CamSettings;
