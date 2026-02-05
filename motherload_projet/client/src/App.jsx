import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Library from './Library';
import Ecosystem from './Ecosystem';
import Scanner from './Scanner';

// Placeholders for now
const Dashboard = () => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="glass-panel p-6 h-32 flex flex-col justify-between">
          <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">Metric {i}</span>
          <span className="text-3xl font-bold text-white">1,240</span>
        </div>
      ))}
    </div>
    <div className="glass-panel p-8 h-[400px] flex items-center justify-center text-slate-500">
      Activity Chart Placeholder
    </div>
  </div>
);



const Calendar = () => (
  <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
    <h2 className="text-2xl text-white font-bold">Academic Calendar</h2>
    <p>Deadline tracking interface coming soon.</p>
  </div>
);

const Scholarships = () => (
  <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
    <h2 className="text-2xl text-white font-bold">Scholarship Finder</h2>
    <p>Opportunity database coming soon.</p>
  </div>
);

const Settings = () => (
  <div className="max-w-2xl mx-auto glass-panel p-8 space-y-6">
    <h2 className="text-2xl text-white font-bold mb-6">Settings</h2>
    <div className="space-y-4">
      <div className="flex justify-between items-center p-4 bg-slate-800/50 rounded-lg">
        <span>UQAR Proxy URL</span>
        <span className="text-slate-400 text-sm">configured in .env</span>
      </div>
      <div className="flex justify-between items-center p-4 bg-slate-800/50 rounded-lg">
        <span>Unpaywall Email</span>
        <span className="text-slate-400 text-sm">configured in .env</span>
      </div>
    </div>
  </div>
)

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/library" element={<Library />} />
          <Route path="/ecosystem" element={<Ecosystem />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/scholarships" element={<Scholarships />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
