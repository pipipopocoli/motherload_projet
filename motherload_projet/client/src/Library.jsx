import { useState, useEffect } from 'react'

const Library = () => {
    const [articles, setArticles] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetch('http://127.0.0.1:8000/api/library')
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    setError(data.error)
                } else {
                    setArticles(data.articles || [])
                }
                setLoading(false)
            })
            .catch(err => {
                setError("Failed to fetch library")
                setLoading(false)
            })
    }, [])

    if (loading) return <div className="p-10 text-center text-slate-400">Scanning Archives...</div>
    if (error) return <div className="p-10 text-center text-red-400">Error: {error}</div>

    return (
        <div className="w-full h-full p-6 flex flex-col gap-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-white">The Vault <span className="text-sm font-normal text-slate-400 ml-2">({articles.length} items)</span></h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto pr-2 pb-20 custom-scrollbar">
                {articles.map((article, idx) => (
                    <div key={idx} className="glass-panel p-4 flex flex-col gap-2 hover:bg-slate-800/60 transition-colors group cursor-pointer">
                        <div className="flex justify-between items-start">
                            <span className="text-xs uppercase font-bold text-violet-400 bg-violet-400/10 px-2 py-0.5 rounded">{article.type || 'Unknown'}</span>
                            {article.year && <span className="text-xs text-slate-500">{article.year}</span>}
                        </div>

                        <h3 className="font-medium text-slate-100 line-clamp-2 leading-tight group-hover:text-violet-300 transition-colors">
                            {article.title || 'Untitled'}
                        </h3>

                        <div className="mt-auto pt-2 border-t border-white/5 flex justify-between items-center">
                            <span className="text-xs text-slate-400 truncate max-w-[150px]">{article.authors || 'Unknown Author'}</span>
                            {article.pdf_path ? (
                                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_5px_rgba(52,211,153,0.5)]" title="PDF Available"></span>
                            ) : (
                                <span className="w-2 h-2 rounded-full bg-slate-600" title="No PDF"></span>
                            )}
                        </div>
                    </div>
                ))}

                {articles.length === 0 && (
                    <div className="col-span-full text-center py-20 text-slate-500">
                        The Vault is empty. Ingest some PDFs to begin.
                    </div>
                )}
            </div>
        </div>
    )
}

export default Library
