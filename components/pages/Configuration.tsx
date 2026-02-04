import React, { useState, useEffect } from 'react';

interface ProviderConfig {
  type: 'openai' | 'ollama';
  apiKey?: string;
  baseUrl?: string;
  model: string;
}

interface ConfigurationProps {
  onConfigSave?: (baseline: ProviderConfig, target: ProviderConfig) => void;
}

const Configuration: React.FC<ConfigurationProps> = ({ onConfigSave }) => {
  const [baselineConfig, setBaselineConfig] = useState<ProviderConfig>({
    type: 'openai',
    apiKey: '',
    model: 'gpt-4o',
  });

  const [targetConfig, setTargetConfig] = useState<ProviderConfig>({
    type: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'gpt-oss:latest',
  });

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [testStatus, setTestStatus] = useState<{ baseline: string; target: string }>({ baseline: '', target: '' });

  // Load saved config on mount
  useEffect(() => {
    const savedBaseline = localStorage.getItem('llm_eval_baseline');
    const savedTarget = localStorage.getItem('llm_eval_target');
    if (savedBaseline) setBaselineConfig(JSON.parse(savedBaseline));
    if (savedTarget) setTargetConfig(JSON.parse(savedTarget));
  }, []);

  const handleSave = () => {
    setSaveStatus('saving');
    try {
      localStorage.setItem('llm_eval_baseline', JSON.stringify(baselineConfig));
      localStorage.setItem('llm_eval_target', JSON.stringify(targetConfig));
      setSaveStatus('saved');
      if (onConfigSave) onConfigSave(baselineConfig, targetConfig);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
    }
  };

  const testConnection = async (which: 'baseline' | 'target') => {
    const config = which === 'baseline' ? baselineConfig : targetConfig;
    const setStatus = (msg: string) => setTestStatus(prev => ({ ...prev, [which]: msg }));

    setStatus('Testing...');

    try {
      // Use the correct backend URL and endpoint
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/api/evaluation/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (data.status === 'success') {
        setStatus('Connected successfully!');
      } else {
        setStatus(`Failed: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setStatus(`Backend error: ${errorMsg}`);
    }

    setTimeout(() => setStatus(''), 5000);
  };

  const renderProviderForm = (
    config: ProviderConfig,
    setConfig: React.Dispatch<React.SetStateAction<ProviderConfig>>,
    label: string,
    which: 'baseline' | 'target'
  ) => (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{label}</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          which === 'baseline' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {which === 'baseline' ? 'Reference Model' : 'Model to Test'}
        </span>
      </div>

      {/* Provider Type Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Provider Type</label>
        <div className="flex gap-4">
          <label className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 cursor-pointer transition-all ${
            config.type === 'openai' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
          }`}>
            <input
              type="radio"
              name={`${which}-provider`}
              value="openai"
              checked={config.type === 'openai'}
              onChange={() => setConfig({ ...config, type: 'openai', model: 'gpt-4o' })}
              className="sr-only"
            />
            <span className="text-xl">&#127760;</span>
            <span className="font-medium">OpenAI API</span>
          </label>
          <label className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 cursor-pointer transition-all ${
            config.type === 'ollama' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
          }`}>
            <input
              type="radio"
              name={`${which}-provider`}
              value="ollama"
              checked={config.type === 'ollama'}
              onChange={() => setConfig({ ...config, type: 'ollama', model: 'gpt-oss:latest', baseUrl: 'http://localhost:11434' })}
              className="sr-only"
            />
            <span className="text-xl">&#128049;</span>
            <span className="font-medium">Ollama (Local)</span>
          </label>
        </div>
      </div>

      {/* OpenAI Config */}
      {config.type === 'openai' && (
        <>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">API Key</label>
            <input
              type="password"
              value={config.apiKey || ''}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              placeholder="sk-..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
            <select
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gpt-4o">GPT-4o (Recommended)</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
        </>
      )}

      {/* Ollama Config */}
      {config.type === 'ollama' && (
        <>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Base URL</label>
            <input
              type="text"
              value={config.baseUrl || ''}
              onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
              placeholder="http://localhost:11434"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Model Name</label>
            <select
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gpt-oss:latest">gpt-oss:latest (13 GB)</option>
              <option value="qwen2.5:7b">qwen2.5:7b (4.7 GB)</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Available models on your Ollama instance</p>
          </div>
        </>
      )}

      {/* Test Connection Button */}
      <button
        onClick={() => testConnection(which)}
        className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
      >
        Test Connection
      </button>
      {testStatus[which] && (
        <p className={`text-sm mt-2 ${testStatus[which].includes('success') ? 'text-green-600' : 'text-amber-600'}`}>
          {testStatus[which]}
        </p>
      )}
    </div>
  );

  return (
    <div className="animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-2">API Configuration</h2>
        <p className="text-gray-600">Configure your baseline and target LLM providers for evaluation</p>
      </div>

      {/* Provider Forms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderProviderForm(baselineConfig, setBaselineConfig, 'Baseline Model', 'baseline')}
        {renderProviderForm(targetConfig, setTargetConfig, 'Target Model', 'target')}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className={`px-8 py-3 rounded-lg font-semibold transition-all ${
            saveStatus === 'saved'
              ? 'bg-green-500 text-white'
              : saveStatus === 'error'
              ? 'bg-red-500 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : 'Save Configuration'}
        </button>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
        <h4 className="font-semibold text-blue-800 mb-1">How it works</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>1. Set your <strong>Baseline Model</strong> (typically OpenAI GPT-4) as the reference</li>
          <li>2. Set your <strong>Target Model</strong> (the model you want to evaluate)</li>
          <li>3. Go to Evaluation tab to run tests and compare results</li>
        </ul>
      </div>
    </div>
  );
};

export default Configuration;
