import { useState } from 'react';
import { ScanLine, Play, FileText, Activity } from 'lucide-react';

const Scanner = () => {
    const [status, setStatus] = useState("Idle");
    const [logs, setLogs] = useState([]);
    const [torStatus, setTorStatus] = useState({ status: "checking" });

    const checkTor = () => {
        fetch('http://127.0.0.1:8000/api/tor/status')
            .then(res => res.json())
            .then(data => setTorStatus(data))
            .catch(() => setTorStatus({ status: "failed" }));
    };

    const startDemo = () => {
        setStatus("Running...");
        setLogs(prev => ["Starting demo scan...", ...prev]);

        fetch('http://127.0.0.1:8000/api/scanner/demo', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    setStatus("Error");
                    setLogs(prev => [`Error: ${data.error}`, ...prev]);
                } else {
                    setLogs(prev => [data.message, ...prev]);
                    // Mock progress updates for demo feel
                    setTimeout(() => setLogs(p => ["Found DOI 10.1038/nature123 -> OA: Yes", ...p]), 2000);
                    setTimeout(() => setLogs(p => ["Found DOI 10.1126/science.456 -> OA: No", ...p]), 4000);
                    setTimeout(() => setLogs(p => ["Download complete. Check 'demo_scan' collection.", ...p]), 6000);
                    setTimeout(() => setStatus("Complete"), 6000);
                }
            })
            .catch(err => {
                setStatus("Error");
                setLogs(prev => ["Failed to connect to backend.", ...prev]);
            });
    };

    return (
        <div className="flex flex-col gap-6 max-w-4xl mx-auto">
            <header>
                <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                    <ScanLine className="text-pink-500" /> Scanner Dashboard
                </h2>
                <p className="text-slate-400 mt-2">Manage your data mining operations. Ingest PDFs or batch download articles.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Actions Panel */}
                <div className="glass-panel p-6 space-y-6">
                    <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>

                    <button
                        onClick={startDemo}
                        disabled={status === "Running..."}
                        className="w-full p-4 rounded-xl bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white font-bold flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-pink-500/20"
                    >
                        <Play fill="currentColor" />
                        {status === "Running..." ? "Scanning..." : "Start Demo Batch"}
                    </button>

                    <div className="p-4 border border-dashed border-white/10 rounded-xl flex flex-col items-center justify-center text-slate-500 gap-2 hover:bg-white/5 transition-colors cursor-pointer h-32">
                        <FileText size={24} />
                        <span>Drop CSV file here to scan</span>
                    </div>
                </div>

                {/* Status Panel */}
                <div className="glass-panel p-6 flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-bold text-white">Live Logs</h3>
                        <div className="flex gap-2">
                            <button onClick={checkTor} className={`text-xs px-2 py-1 rounded border ${torStatus.status === 'connected' ? 'border-emerald-500 text-emerald-500' : 'border-red-500 text-red-500'}`}>
                                Tor: {torStatus.status}
                            </button>
                            <span className={`text-xs px-2 py-1 rounded-full border ${status === "Running..." ? "border-amber-500 text-amber-500 animate-pulse" :
                                    status === "Complete" ? "border-emerald-500 text-emerald-500" :
                                        "border-slate-600 text-slate-600"
                                }`}>
                                {status}
                            </span>
                        </div>
                    </div>

                    <div className="flex-1 bg-slate-950/50 rounded-lg p-4 font-mono text-sm overflow-y-auto max-h-[300px] border border-white/5 space-y-2">
                        {logs.length === 0 ? (
                            <span className="text-slate-600 italic">Ready to engage warp drive.</span>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="flex gap-2">
                                    <span className="text-slate-600">[{new Date().toLocaleTimeString()}]</span>
                                    <span className={i === 0 ? "text-white font-bold" : "text-slate-400"}>{log}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-panel p-6 flex items-center justify-between">
                    <div>
                        <p className="text-slate-400 text-xs uppercase font-bold">Success Rate</p>
                        <p className="text-2xl font-bold text-white">68%</p>
                    </div>
                    <Activity className="text-emerald-500" />
                </div>
                {/* Placeholders for more stats */}
            </div>
        </div>
    );
};

export default Scanner;
