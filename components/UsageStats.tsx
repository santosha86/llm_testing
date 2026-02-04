import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../constants';

interface UsageStatsData {
  queries_processed: number;
  user_satisfaction: string;
  avg_response_time: string;
  unique_users: number;
  top_categories: Record<string, string>;
}

const UsageStats: React.FC = () => {
  const [data, setData] = useState<UsageStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/usage-stats`, {
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
          console.error('Failed to fetch usage stats:', err);
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
      <div className="mt-6">
        <div className="bg-[#0f3460] text-white px-5 py-3 rounded-t-xl inline-flex items-center gap-2 border-t border-x border-indigo-500/20">
          <span className="text-lg">📈</span>
          <span className="font-semibold">Usage Statistics</span>
        </div>
        <div className="bg-gradient-to-br from-[#1a1a2e] to-[#16213e] rounded-b-xl rounded-tr-xl p-6 border border-indigo-500/20 shadow-2xl flex items-center justify-center min-h-[150px]">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mt-6">
        <div className="bg-[#0f3460] text-white px-5 py-3 rounded-t-xl inline-flex items-center gap-2 border-t border-x border-indigo-500/20">
          <span className="text-lg">📈</span>
          <span className="font-semibold">Usage Statistics</span>
        </div>
        <div className="bg-gradient-to-br from-[#1a1a2e] to-[#16213e] rounded-b-xl rounded-tr-xl p-6 border border-indigo-500/20 shadow-2xl flex items-center justify-center min-h-[150px] text-red-400 text-sm">
          {error || 'Failed to load data. Make sure the backend is running.'}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <div className="bg-[#0f3460] text-white px-5 py-3 rounded-t-xl inline-flex items-center gap-2 border-t border-x border-indigo-500/20">
        <span className="text-lg">📈</span>
        <span className="font-semibold">Usage Statistics</span>
      </div>

      <div className="bg-gradient-to-br from-[#1a1a2e] to-[#16213e] rounded-b-xl rounded-tr-xl p-6 border border-indigo-500/20 shadow-2xl grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Week Stats */}
        <div className="bg-[#1a1a2e]/50 rounded-xl p-5 border-l-4 border-blue-400 border-t border-r border-b border-indigo-500/10 shadow-lg">
          <h4 className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
            📊 This Week's Stats
          </h4>
          <ul className="space-y-2">
            <li className="text-sm text-slate-300 flex items-center gap-2">
              <span className="text-indigo-500">•</span> {data.queries_processed} queries processed
            </li>
            <li className="text-sm text-slate-300 flex items-center gap-2">
              <span className="text-indigo-500">•</span> {data.user_satisfaction} user satisfaction
            </li>
            <li className="text-sm text-slate-300 flex items-center gap-2">
              <span className="text-indigo-500">•</span> {data.avg_response_time} avg response time
            </li>
            <li className="text-sm text-slate-300 flex items-center gap-2">
              <span className="text-indigo-500">•</span> {data.unique_users} unique users
            </li>
          </ul>
        </div>

        {/* Top Categories */}
        <div className="bg-[#1a1a2e]/50 rounded-xl p-5 border-l-4 border-pink-400 border-t border-r border-b border-indigo-500/10 shadow-lg">
          <h4 className="text-pink-400 font-semibold mb-3 flex items-center gap-2">
            📊 Top Query Categories
          </h4>
          <ul className="space-y-2">
            {Object.entries(data.top_categories).map(([category, percentage], i) => (
              <li key={i} className="text-sm text-slate-300 flex items-center gap-2">
                <span className="text-indigo-500">•</span> {percentage} {category}
              </li>
            ))}
          </ul>
        </div>

      </div>
    </div>
  );
};

export default UsageStats;
