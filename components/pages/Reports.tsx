import React, { useState, useEffect } from 'react';

interface TestResult {
  testId: string;
  category: string;
  question: string;
  expected: string;
  baselineAnswer?: string;
  targetAnswer?: string;
  baselinePass?: boolean;
  targetPass?: boolean;
  baselineLatency?: number;
  targetLatency?: number;
}

interface EvaluationRun {
  id: number;
  category: string;
  timestamp: string;
  results: TestResult[];
}

const Reports: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    const savedRuns = localStorage.getItem('llm_eval_results');
    if (savedRuns) {
      const parsed = JSON.parse(savedRuns);
      setRuns(parsed);
      if (parsed.length > 0) {
        setSelectedRun(parsed[parsed.length - 1]);
      }
    }
  }, []);

  const calculateStats = (results: TestResult[]) => {
    const baselinePass = results.filter(r => r.baselinePass).length;
    const targetPass = results.filter(r => r.targetPass).length;
    const total = results.length;
    return {
      baselinePass,
      targetPass,
      total,
      baselineRate: Math.round((baselinePass / total) * 100),
      targetRate: Math.round((targetPass / total) * 100),
      gap: Math.round((baselinePass / total) * 100) - Math.round((targetPass / total) * 100),
    };
  };

  const aggregateAllRuns = () => {
    const allResults = runs.flatMap(r => r.results);
    return calculateStats(allResults);
  };

  const clearResults = () => {
    if (confirm('Are you sure you want to clear all evaluation results?')) {
      localStorage.removeItem('llm_eval_results');
      setRuns([]);
      setSelectedRun(null);
    }
  };

  const exportReport = () => {
    const report = {
      generatedAt: new Date().toISOString(),
      summary: aggregateAllRuns(),
      runs: runs,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm-evaluation-report-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  if (runs.length === 0) {
    return (
      <div className="animate-in fade-in duration-500 space-y-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-2">Evaluation Reports</h2>
          <p className="text-gray-600">View and analyze evaluation results</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <div className="text-6xl mb-4">&#128202;</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No Evaluation Results Yet</h3>
          <p className="text-gray-600 mb-4">Run an evaluation from the Evaluation tab to see results here</p>
        </div>
      </div>
    );
  }

  const overallStats = aggregateAllRuns();

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Evaluation Reports</h2>
          <p className="text-gray-600">Aggregated results from {runs.length} evaluation run(s)</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportReport}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Export JSON
          </button>
          <button
            onClick={clearResults}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
          <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide">Baseline Model</h3>
          <div className="mt-2 flex items-baseline">
            <span className="text-4xl font-bold text-green-600">{overallStats.baselineRate}%</span>
            <span className="ml-2 text-sm text-gray-500">Pass Rate</span>
          </div>
          <p className="mt-2 text-sm text-gray-600">{overallStats.baselinePass} of {overallStats.total} tests passed</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-red-500">
          <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide">Target Model</h3>
          <div className="mt-2 flex items-baseline">
            <span className="text-4xl font-bold text-red-600">{overallStats.targetRate}%</span>
            <span className="ml-2 text-sm text-gray-500">Pass Rate</span>
          </div>
          <p className="mt-2 text-sm text-gray-600">{overallStats.targetPass} of {overallStats.total} tests passed</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-amber-500">
          <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide">Performance Gap</h3>
          <div className="mt-2 flex items-baseline">
            <span className="text-4xl font-bold text-amber-600">{overallStats.gap}%</span>
            <span className="ml-2 text-sm text-gray-500">Difference</span>
          </div>
          <p className="mt-2 text-sm text-gray-600">Target underperforms baseline</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
          <h3 className="text-gray-500 text-sm font-medium uppercase tracking-wide">Total Tests</h3>
          <div className="mt-2 flex items-baseline">
            <span className="text-4xl font-bold text-blue-600">{overallStats.total}</span>
            <span className="ml-2 text-sm text-gray-500">Executed</span>
          </div>
          <p className="mt-2 text-sm text-gray-600">Across {runs.length} evaluation run(s)</p>
        </div>
      </div>

      {/* Critical Finding */}
      {overallStats.gap > 20 && (
        <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-r-lg">
          <div className="flex items-start">
            <span className="text-3xl mr-4">&#9888;&#65039;</span>
            <div>
              <h3 className="text-lg font-semibold text-red-800">Critical Finding</h3>
              <p className="text-red-700 mt-1">
                Target Model shows a <strong>{overallStats.gap}% lower pass rate</strong> compared to baseline.
                This gap indicates significant capability limitations that may impact production use cases.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Run History */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h3 className="font-semibold text-gray-800">Evaluation Run History</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {runs.slice().reverse().map((run) => {
            const stats = calculateStats(run.results);
            return (
              <button
                key={run.id}
                onClick={() => setSelectedRun(run)}
                className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                  selectedRun?.id === run.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium text-gray-800">{run.category.toUpperCase()} Tests</span>
                    <span className="text-sm text-gray-500 ml-3">
                      {new Date(run.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-4">
                    <span className="text-sm">
                      <span className="text-green-600 font-medium">{stats.baselinePass}/{stats.total}</span>
                      <span className="text-gray-400 mx-1">|</span>
                      <span className="text-red-600 font-medium">{stats.targetPass}/{stats.total}</span>
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Run Details */}
      {selectedRun && (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="font-semibold text-gray-800">
              Details: {selectedRun.category.toUpperCase()} Tests
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({new Date(selectedRun.timestamp).toLocaleString()})
              </span>
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">Test ID</th>
                  <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">Question</th>
                  <th className="py-3 px-4 text-left text-xs font-semibold text-gray-600 uppercase">Expected</th>
                  <th className="py-3 px-4 text-center text-xs font-semibold text-gray-600 uppercase">Baseline</th>
                  <th className="py-3 px-4 text-center text-xs font-semibold text-gray-600 uppercase">Target</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {selectedRun.results.map((result) => (
                  <tr key={result.testId} className="hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{result.testId}</span>
                    </td>
                    <td className="py-4 px-4 max-w-xs">
                      <p className="text-sm text-gray-900 truncate" title={result.question}>{result.question}</p>
                    </td>
                    <td className="py-4 px-4">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">{result.expected}</code>
                    </td>
                    <td className="py-4 px-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        result.baselinePass ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {result.baselinePass ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        result.targetPass ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {result.targetPass ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
