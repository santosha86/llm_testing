import React from 'react';
import { COLOR_MAP, ROADMAP_DATA, VALUE_ADDED_CARDS } from '../constants';

const ValueAddedTab: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {VALUE_ADDED_CARDS.map((card, idx) => {
          const colors = COLOR_MAP[card.color];
          
          return (
            <div
              key={idx}
              className={`
                relative flex flex-col h-full p-5 rounded-2xl transition-all duration-300 hover:-translate-y-1
                bg-gradient-to-br from-[#1a1a2e] to-[#16213e]
                border-l-4 ${colors.border}
                shadow-xl hover:shadow-2xl ${colors.shadow}
                border-t border-r border-b border-white/5
              `}
            >
              <h3 className={`text-sm font-bold mb-3 flex items-center gap-2 ${colors.title}`}>
                {card.title}
              </h3>

              {card.title.includes("Target Performance") ? (
                <div className="flex flex-col items-center justify-center text-center flex-1">
                  <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-green-400 to-green-600 drop-shadow-lg">
                    70%
                  </div>
                  <div className="text-indigo-300 font-medium mt-2 text-xs">Answer Accuracy</div>
                  <div className="text-slate-400 text-[10px] mt-2 leading-relaxed">
                    Initial PoC target based on<br />current data quality and scope
                  </div>
                  <div className="text-slate-500 text-[10px] mt-1">(Target range: 90%)</div>
                </div>
              ) : (
                <ul className="space-y-2 flex-1">
                  {card.items.map((item, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                      <span className="text-indigo-400 font-bold mt-0.5">•</span>
                      <span dangerouslySetInnerHTML={{ __html: item.replace(/<b/g, '<span class="font-bold text-white"').replace(/<\/b>/g, '</span>') }} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>

      {/* Roadmap Section */}
      <div className="rounded-xl overflow-hidden shadow-2xl border border-indigo-500/20">
        <div className="bg-gradient-to-r from-[#1a1a2e] to-[#16213e] p-5 border-b border-indigo-500/20">
          <h2 className="text-lg font-semibold text-white">📋 POC vs Production Roadmap</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-300 bg-[#16213e]">
            <thead className="text-xs uppercase bg-[#0f3460] text-indigo-200">
              <tr>
                <th className="px-6 py-4">Feature</th>
                <th className="px-6 py-4">POC (Current)</th>
                <th className="px-6 py-4">Production Vision</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-indigo-500/10">
              {ROADMAP_DATA.map((row, idx) => (
                row.feature === "*" ? (
                  <tr key={idx} className="hover:bg-indigo-500/5 transition-colors">
                    <td colSpan={3} className="px-6 py-2 text-xs text-slate-400 italic">
                      <span className="font-medium">*</span> {row.prodVision}
                    </td>
                  </tr>
                ) : (
                  <tr key={idx} className="hover:bg-indigo-500/5 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">{row.feature}</td>
                    <td className={`px-6 py-4 font-medium ${row.pocClass === 'green' ? 'text-green-400' : row.pocClass === 'orange' ? 'text-orange-400' : 'text-red-400'}`}>
                      {row.pocStatus}
                    </td>
                    <td className={`px-6 py-4 font-medium ${row.prodClass === 'green' ? 'text-green-400' : 'text-orange-400'}`}>
                      {row.prodVision}{row.feature.includes("Answer Accuracy") && <sup className="text-[10px]">*</sup>}
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gradient-to-r from-teal-800 to-teal-700 text-yellow-400 text-center p-4 rounded-xl text-sm font-medium shadow-lg">
        © 2025 SPB Logistics Intelligence Platform - Data-Driven Chatbot POC v1.0 | Connected to: ODW Online • SAP Finance • Telematics
      </div>
    </div>
  );
};

export default ValueAddedTab;