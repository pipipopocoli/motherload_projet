import { useState, useEffect } from 'react'
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts'
import { RefreshCw, BookOpen, Layers } from 'lucide-react'

const Ecosystem = () => {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedNode, setSelectedNode] = useState(null)
    const [error, setError] = useState(null)

    const fetchEcosystem = (scan = false) => {
        setLoading(true)
        const url = scan ? 'http://127.0.0.1:8000/api/ecosystem/scan' : 'http://127.0.0.1:8000/api/ecosystem'
        const method = scan ? 'POST' : 'GET'

        fetch(url, { method })
            .then(res => res.json())
            .then(json => {
                if (json.error) {
                    setError(json.error)
                } else {
                    setData(transformData(json))
                }
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setError("Failed to fetch ecosystem")
                setLoading(false)
            })
    }

    useEffect(() => {
        fetchEcosystem()
    }, [])

    // Transform flat node list to hierarchy for Treemap
    const transformData = (json) => {
        if (!json.nodes) return []

        const nodes = json.nodes
        const packages = nodes.filter(n => n.type === 'package')
        const modules = nodes.filter(n => n.type === 'module')

        // Build hierarchy: Root -> Package -> Module
        const root = {
            name: 'Motherload',
            children: packages.map(pkg => ({
                name: pkg.name || 'root',
                size: pkg.completion || 10, // Size by completion or complexity
                children: modules.filter(m => m.parent === pkg.id).map(mod => ({
                    name: mod.name,
                    size: mod.completion || 10,
                    ...mod
                }))
            }))
        }
        return [root]
    }

    const CustomContent = (props) => {
        const { root, depth, x, y, width, height, index, name, completion } = props;

        return (
            <g>
                <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    style={{
                        fill: depth < 2 ? 'transparent' : '#1e293b', // Slate 800
                        stroke: '#fff',
                        strokeWidth: 2 / (depth + 1e-10),
                        strokeOpacity: 0.1,
                    }}
                />
                {depth === 2 && width > 50 && height > 30 && (
                    <foreignObject x={x} y={y} width={width} height={height}>
                        <div className="w-full h-full p-2 flex flex-col justify-center items-center text-center overflow-hidden">
                            <span className="text-xs font-bold text-slate-200 truncate w-full">{name}</span>
                            <span className={`text-[10px] ${completion > 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                {completion}%
                            </span>
                        </div>
                    </foreignObject>
                )}
            </g>
        );
    };

    if (loading && !data) return <div className="p-10 text-center text-slate-400">Scanning Biome...</div>
    if (error) return <div className="p-10 text-center text-red-400">Error: {error}</div>

    return (
        <div className="w-full h-full p-6 flex flex-col gap-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-white flex items-center gap-2">
                    <Layers className="text-violet-400" /> Ecosystem
                </h2>
                <div className="flex gap-2">
                    <button onClick={() => fetchEcosystem(true)} className="glass-button flex items-center gap-2 text-sm">
                        <RefreshCw size={14} /> Re-Scan
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                {/* Visualizer */}
                <div className="lg:col-span-2 glass-panel p-4 h-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <Treemap
                            data={data}
                            dataKey="size"
                            aspectRatio={4 / 3}
                            stroke="#fff"
                            fill="#8884d8"
                            content={<CustomContent />}
                            onClick={(node) => setSelectedNode(node)}
                        >
                            <Tooltip content={({ payload }) => {
                                if (!payload || !payload.length) return null;
                                const d = payload[0].payload;
                                return (
                                    <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs">
                                        <p className="font-bold text-violet-300">{d.name}</p>
                                        <p>Completion: {d.completion}%</p>
                                    </div>
                                )
                            }} />
                        </Treemap>
                    </ResponsiveContainer>
                    <p className="absolute bottom-2 left-4 text-xs text-slate-500">Click a module to see details</p>
                </div>

                {/* Detail View */}
                <div className="glass-panel p-6 flex flex-col gap-4 overflow-y-auto">
                    {selectedNode ? (
                        <>
                            <div>
                                <h3 className="text-xl font-bold text-white">{selectedNode.name}</h3>
                                <span className="text-xs uppercase tracking-wider text-slate-500">{selectedNode.type || 'Module'}</span>
                            </div>

                            <div className="space-y-4">
                                <div className="p-3 bg-slate-800/50 rounded border border-white/5">
                                    <h4 className="text-sm font-medium text-violet-300 mb-1">Summary</h4>
                                    <p className="text-sm text-slate-300 leading-relaxed">{selectedNode.summary || 'No summary available.'}</p>
                                </div>

                                <div className="p-3 bg-slate-800/50 rounded border border-white/5">
                                    <h4 className="text-sm font-medium text-pink-300 mb-1">Outputs</h4>
                                    <p className="text-sm text-slate-300 leading-relaxed">{selectedNode.outputs || 'No defined outputs.'}</p>
                                </div>

                                <div className="mt-4">
                                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                                        <span>Completion</span>
                                        <span>{selectedNode.completion}%</span>
                                    </div>
                                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-violet-500 to-pink-500"
                                            style={{ width: `${selectedNode.completion}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
                            <BookOpen size={48} className="opacity-20" />
                            <p>Select a module from the map to view its DNA.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Ecosystem
