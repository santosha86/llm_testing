import React from 'react';

interface DashboardProps {
  onNavigate: (tab: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-700 rounded-xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-2">LLM Evaluation Tool</h2>
        <p className="text-blue-200">
          Compare baseline models (OpenAI GPT-4) against target models to measure capability gaps
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <button
          onClick={() => onNavigate('configuration')}
          className="bg-white rounded-xl shadow-lg p-6 text-left hover:shadow-xl transition-shadow border-l-4 border-blue-500"
        >
          <div className="text-3xl mb-3">1</div>
          <h3 className="font-semibold text-gray-800 mb-2">Configure APIs</h3>
          <p className="text-sm text-gray-600">Set up OpenAI or Ollama as your baseline and target models</p>
        </button>

        <button
          onClick={() => onNavigate('evaluation')}
          className="bg-white rounded-xl shadow-lg p-6 text-left hover:shadow-xl transition-shadow border-l-4 border-green-500"
        >
          <div className="text-3xl mb-3">2</div>
          <h3 className="font-semibold text-gray-800 mb-2">Run Evaluation</h3>
          <p className="text-sm text-gray-600">Execute batch tests across Math, Logic, and Retrieval categories</p>
        </button>

        <button
          onClick={() => onNavigate('reports')}
          className="bg-white rounded-xl shadow-lg p-6 text-left hover:shadow-xl transition-shadow border-l-4 border-purple-500"
        >
          <div className="text-3xl mb-3">3</div>
          <h3 className="font-semibold text-gray-800 mb-2">View Reports</h3>
          <p className="text-sm text-gray-600">Analyze results and generate comparison reports</p>
        </button>
      </div>

      {/* Last Run Summary (placeholder) */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Last Evaluation Run</h3>
        <div className="text-gray-500 text-center py-8">
          <div className="text-4xl mb-3">---</div>
          <p>No evaluation runs yet. Configure your APIs and run an evaluation to see results here.</p>
        </div>
      </div>

      {/* Test Categories Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">&#128290;</span>
            <h3 className="font-semibold text-gray-800">Math Tests</h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">6 tests covering numerical calculations, energy computations, and financial math</p>
          <div className="text-xs text-gray-400">Examples: Annual energy output, revenue calculations, capacity factors</div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">&#129504;</span>
            <h3 className="font-semibold text-gray-800">Logic Tests</h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">6 tests covering multi-condition logic, eligibility rules, and decision trees</p>
          <div className="text-xs text-gray-400">Examples: Bidder eligibility, compliance checks, rule evaluation</div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">&#128196;</span>
            <h3 className="font-semibold text-gray-800">Retrieval Tests</h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">6 tests covering long-context retrieval and document understanding</p>
          <div className="text-xs text-gray-400">Examples: Extract specific facts, cross-reference data, summarize documents</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
