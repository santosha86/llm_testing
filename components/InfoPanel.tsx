import React, { useState, useEffect } from 'react';
import { Check, X, Search, BarChart2, Lightbulb, TrendingUp } from 'lucide-react';
import { API_BASE_URL } from '../constants';

// Icon mapping for capabilities
const CAPABILITY_ICONS: Record<string, string> = {
  search: '🔍',
  chart: '📊',
  lightbulb: '💡',
  trending: '📈',
};

interface ProcessComparison {
  old_way: string[];
  new_way: string[];
}

interface BusinessValueRow {
  metric: string;
  before: string;
  after: string;
}

interface KeyMetric {
  value: string;
  label: string;
}

interface Capability {
  icon: string;
  label: string;
}

interface AIOverviewData {
  process_comparison: ProcessComparison;
  business_value: BusinessValueRow[];
  key_metrics: KeyMetric[];
  capabilities: Capability[];
  language_support: string;
}

const InfoPanel: React.FC = () => {
  const [data, setData] = useState<AIOverviewData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/ai-overview`, {
          signal: controller.signal,
          headers: {
            'ngrok-skip-browser-warning': 'true'
          }
        });
        if (response.ok) {
          const result = await response.json();
          setData(result);
        } else {
          throw new Error('Failed to fetch data');
        }
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          console.error('Failed to fetch AI overview:', err);
          setError('Failed to load data');
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };
    fetchData();

    return () => controller.abort();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col rounded-2xl overflow-hidden shadow-2xl border border-indigo-500/20 bg-gradient-to-b from-[#1a1a2e] to-[#16213e] h-[700px]">
        <div className="bg-gradient-to-r from-[#0f3460] to-[#16213e] p-4 text-center border-b border-indigo-500/20 shrink-0">
          <h2 className="text-white font-semibold text-base">📊 Conversational Chatbot Overview</h2>
          <p className="text-indigo-300 text-xs mt-1">Before vs After Comparison</p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col rounded-2xl overflow-hidden shadow-2xl border border-indigo-500/20 bg-gradient-to-b from-[#1a1a2e] to-[#16213e] h-[700px]">
        <div className="bg-gradient-to-r from-[#0f3460] to-[#16213e] p-4 text-center border-b border-indigo-500/20 shrink-0">
          <h2 className="text-white font-semibold text-base">📊 Conversational Chatbot Overview</h2>
        </div>
        <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
          {error || 'Failed to load data. Make sure the backend is running.'}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col rounded-2xl overflow-hidden shadow-2xl border border-indigo-500/20 bg-gradient-to-b from-[#1a1a2e] to-[#16213e] h-[700px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0f3460] to-[#16213e] p-4 text-center border-b border-indigo-500/20 shrink-0">
        <h2 className="text-white font-semibold text-base">📊 Conversational Chatbot Overview</h2>
        <p className="text-indigo-300 text-xs mt-1">Before vs After Comparison</p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">

        {/* Comparison Section */}
        <div className="border-b border-indigo-500/20 pb-4">
          <div className="bg-[#0f3460] p-2.5 rounded-lg mb-3 border border-indigo-500/20">
            <h3 className="text-white text-sm font-semibold">🔄 Process Comparison</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {/* Old Way */}
            <div className="bg-[#0f3460]/50 border border-red-500/20 p-3 rounded-lg">
              <div className="text-xs font-semibold text-white mb-2 text-center border-b border-red-500/20 pb-2">
                ❌ Old Way (Manual)
              </div>
              <ul className="space-y-1.5 text-[10px] text-slate-300">
                {data.process_comparison.old_way.map((item, i) => (
                  <li key={i} className="flex gap-1.5">
                    <X size={12} className="text-red-400 shrink-0" /> {item}
                  </li>
                ))}
              </ul>
            </div>
            {/* New Way */}
            <div className="bg-[#0f3460]/50 border border-green-500/20 p-3 rounded-lg">
              <div className="text-xs font-semibold text-white mb-2 text-center border-b border-green-500/20 pb-2">
                ✅ New Way (Data-Driven)
              </div>
              <ul className="space-y-1.5 text-[10px] text-slate-300">
                {data.process_comparison.new_way.map((item, i) => (
                  <li key={i} className="flex gap-1.5">
                    <Check size={12} className="text-green-400 shrink-0" /> {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Business Value Table */}
        <div className="border-b border-indigo-500/20 pb-4">
          <div className="bg-[#0f3460] p-2.5 rounded-lg mb-3 border border-indigo-500/20">
            <h3 className="text-white text-sm font-semibold">💰 Business Value</h3>
          </div>
          <div className="bg-[#0f3460]/30 rounded-lg overflow-hidden border border-indigo-500/20">
            <table className="w-full text-[11px] text-slate-300">
              <thead>
                <tr className="bg-[#0f3460] text-white">
                  <th className="p-2 text-left">Metric</th>
                  <th className="p-2 text-center">Before</th>
                  <th className="p-2 text-center">After</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-indigo-500/10">
                {data.business_value.map((row, i) => (
                  <tr key={i}>
                    <td className="p-2 font-medium">{row.metric}</td>
                    <td className="p-2 text-center text-slate-400">{row.before}</td>
                    <td className="p-2 text-center text-green-400 font-bold">{row.after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 p-2 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-[10px] text-green-300 text-center font-medium">
              ✨ Reduces manual effort & enables faster, data-driven decisions
            </p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="border-b border-indigo-500/20 pb-4">
          <div className="bg-[#0f3460] p-2.5 rounded-lg mb-3 border border-indigo-500/20">
            <h3 className="text-white text-sm font-semibold">📈 Key Metrics</h3>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {data.key_metrics.map((m, i) => (
              <div key={i} className="bg-[#0f3460]/40 border border-indigo-500/20 p-3 rounded-lg text-center">
                <div className="text-lg font-bold text-white">{m.value}</div>
                <div className="text-[10px] text-slate-400 font-medium">{m.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Data-Driven Capabilities */}
        <div>
           <div className="bg-[#0f3460] p-2.5 rounded-lg mb-3 border border-indigo-500/20">
            <h3 className="text-white text-sm font-semibold">🎯 Data-Driven Capabilities</h3>
          </div>
          <div className="grid grid-cols-2 gap-2">
             {data.capabilities.map((c, i) => (
                <div key={i} className="bg-[#0f3460]/40 border border-indigo-500/20 p-2 rounded-lg text-center">
                  <div className="text-base mb-1">{CAPABILITY_ICONS[c.icon] || '🔧'}</div>
                  <div className="text-[10px] text-slate-400 font-medium">{c.label}</div>
                </div>
             ))}
             <div className="col-span-2 bg-[#0f3460]/40 border border-indigo-500/20 p-2 rounded-lg text-center">
               <div className="text-base mb-1">🌐</div>
               <div className="text-[10px] text-slate-400 font-medium">{data.language_support}</div>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default InfoPanel;
