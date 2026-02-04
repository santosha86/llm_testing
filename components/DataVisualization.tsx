import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { BarChart2, Table } from 'lucide-react';
import { VisualizationConfig, TableData } from '../types';

interface DataVisualizationProps {
  visualization: VisualizationConfig;
  tableData: TableData;
}

// Truncate long labels for compact display
function truncateLabel(label: string, maxLength: number = 12): string {
  if (!label || label.length <= maxLength) return label;
  return label.substring(0, maxLength - 2) + '..';
}

// Color palette for charts
const COLORS = [
  '#3b82f6', // blue-500
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#06b6d4', // cyan-500
  '#84cc16', // lime-500
  '#f97316', // orange-500
  '#6366f1', // indigo-500
];

// Transform table data into chart-compatible format
function transformData(tableData: TableData, xAxis: string, yAxis: string, yAxisSecondary?: string | null) {
  const xIndex = tableData.columns.indexOf(xAxis);
  const yIndex = tableData.columns.indexOf(yAxis);
  const ySecondaryIndex = yAxisSecondary ? tableData.columns.indexOf(yAxisSecondary) : -1;

  if (xIndex === -1 || yIndex === -1) {
    // Fallback: use first column as x and second as y
    return tableData.rows.map((row) => ({
      name: String(row[0] ?? ''),
      value: Number(row[1]) || 0,
      ...(tableData.columns.length > 2 ? { value2: Number(row[2]) || 0 } : {}),
    }));
  }

  return tableData.rows.map((row) => ({
    name: String(row[xIndex] ?? ''),
    value: Number(row[yIndex]) || 0,
    ...(ySecondaryIndex !== -1 ? { value2: Number(row[ySecondaryIndex]) || 0 } : {}),
  }));
}

// Pivot long-format data for grouped bar charts
// Input:  rows like [["Cancelled", "Vendor A", 10], ["Expired", "Vendor A", 8], ...]
// Output: [{name: "Vendor A", Cancelled: 10, Expired: 8, ...}, ...]
function pivotData(
  tableData: TableData,
  xAxis: string,
  yAxis: string,
  groupBy: string
): { data: any[]; groupValues: string[] } {
  const groupByIndex = tableData.columns.indexOf(groupBy);
  const xIndex = tableData.columns.indexOf(xAxis);
  const yIndex = tableData.columns.indexOf(yAxis);

  if (groupByIndex === -1 || xIndex === -1 || yIndex === -1) {
    return { data: [], groupValues: [] };
  }

  // Get unique group values (e.g., ["Cancelled", "Expired", "Rejected"])
  const groupValues = [...new Set(tableData.rows.map((row) => String(row[groupByIndex])))];

  // Get unique x values (e.g., ["Vendor A", "Vendor B", ...])
  const xValues = [...new Set(tableData.rows.map((row) => String(row[xIndex])))];

  // Create pivoted data
  const pivotedData = xValues.map((x) => {
    const result: any = { name: x };
    groupValues.forEach((group) => {
      const matchingRow = tableData.rows.find(
        (row) => String(row[xIndex]) === x && String(row[groupByIndex]) === group
      );
      result[group] = matchingRow ? Number(matchingRow[yIndex]) || 0 : 0;
    });
    return result;
  });

  return { data: pivotedData, groupValues };
}

// Transform wide-format data for grouped bar charts
// Input:  columns ["Vendor", "cancelled", "expired", "rejected"], rows [["Vendor A", 100, 50, 20], ...]
// Output: [{name: "Vendor A", cancelled: 100, expired: 50, rejected: 20}, ...]
function transformWideData(
  tableData: TableData,
  xAxis: string,
  yAxisList: string[]
): any[] {
  const xIndex = tableData.columns.indexOf(xAxis);

  if (xIndex === -1) {
    return [];
  }

  return tableData.rows.map((row) => {
    const result: any = { name: String(row[xIndex] ?? '') };
    yAxisList.forEach((col) => {
      const colIndex = tableData.columns.indexOf(col);
      result[col] = colIndex !== -1 ? Number(row[colIndex]) || 0 : 0;
    });
    return result;
  });
}

// Custom tooltip for better display (compact version)
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 p-1.5 border border-gray-200 dark:border-gray-700 rounded shadow-lg text-xs max-w-[180px]">
        <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="truncate">
            {truncateLabel(entry.name, 12)}: {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function DataVisualization({ visualization, tableData }: DataVisualizationProps) {
  const [showChart, setShowChart] = useState(true);

  if (!visualization.should_visualize || !visualization.chart_type) {
    return null;
  }

  const data = transformData(
    tableData,
    visualization.x_axis || tableData.columns[0],
    visualization.y_axis || tableData.columns[1],
    visualization.y_axis_secondary
  );

  const yAxisLabel = visualization.y_axis || tableData.columns[1] || 'Value';
  const yAxisSecondaryLabel = visualization.y_axis_secondary || '';

  const renderChart = () => {
    switch (visualization.chart_type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data} margin={{ top: 20, right: 20, left: 10, bottom: 70 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={1} />
                  <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.8} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={80}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickFormatter={(value) => value.length > 18 ? value.substring(0, 16) + '..' : value}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                width={50}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{label}</p>
                        <p className="text-slate-300 text-xs">
                          {yAxisLabel}: <span className="text-blue-400 font-medium">{(payload[0].value as number).toLocaleString()}</span>
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              <Bar
                dataKey="value"
                name={yAxisLabel}
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
                label={{
                  position: 'top',
                  fill: '#94a3b8',
                  fontSize: 9,
                  formatter: (value: number) => value > 0 ? value.toLocaleString() : '',
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'horizontal_bar':
        return (
          <ResponsiveContainer width="100%" height={Math.min(400, Math.max(200, data.length * 32))}>
            <BarChart data={data} layout="vertical" margin={{ top: 15, right: 30, left: 20, bottom: 15 }}>
              <defs>
                <linearGradient id="hBarGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#1d4ed8" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} horizontal={false} />
              <XAxis
                type="number"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <YAxis
                dataKey="name"
                type="category"
                width={120}
                tick={{ fontSize: 11, fill: '#e2e8f0' }}
                tickFormatter={(value) => value.length > 20 ? value.substring(0, 18) + '..' : value}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{label}</p>
                        <p className="text-slate-300 text-xs">
                          {yAxisLabel}: <span className="text-blue-400 font-medium">{(payload[0].value as number).toLocaleString()}</span>
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              <Bar
                dataKey="value"
                name={yAxisLabel}
                fill="url(#hBarGradient)"
                radius={[0, 4, 4, 0]}
                label={{
                  position: 'right',
                  fill: '#94a3b8',
                  fontSize: 10,
                  formatter: (value: number) => value > 0 ? value.toLocaleString() : '',
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data} margin={{ top: 20, right: 20, left: 10, bottom: 70 }}>
              <defs>
                <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="lineGradient2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={80}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickFormatter={(value) => value.length > 18 ? value.substring(0, 16) + '..' : value}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                width={50}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{label}</p>
                        {payload.map((entry: any, index: number) => (
                          <p key={index} className="text-slate-300 text-xs">
                            {entry.name}: <span style={{ color: entry.color }} className="font-medium">{(entry.value as number).toLocaleString()}</span>
                          </p>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              <Line
                type="monotone"
                dataKey="value"
                name={yAxisLabel}
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4, stroke: '#1e3a5f' }}
                activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
              />
              {visualization.y_axis_secondary && (
                <Line
                  type="monotone"
                  dataKey="value2"
                  name={yAxisSecondaryLabel}
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ fill: '#10b981', strokeWidth: 2, r: 4, stroke: '#064e3b' }}
                  activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        // Calculate total for percentage display
        const total = data.reduce((sum, item) => sum + item.value, 0);

        // Custom label with leader lines for better readability
        const renderCustomizedLabel = ({
          cx,
          cy,
          midAngle,
          innerRadius,
          outerRadius,
          percent,
          index,
          name,
          value,
        }: any) => {
          const RADIAN = Math.PI / 180;

          // Skip very small slices (less than 1%)
          if (percent < 0.01) return null;

          // Calculate label position - further out for better spacing
          const radius = outerRadius + 25;
          const x = cx + radius * Math.cos(-midAngle * RADIAN);
          const y = cy + radius * Math.sin(-midAngle * RADIAN);

          // Calculate line start point (on the pie edge)
          const lineStartRadius = outerRadius + 5;
          const lineX1 = cx + lineStartRadius * Math.cos(-midAngle * RADIAN);
          const lineY1 = cy + lineStartRadius * Math.sin(-midAngle * RADIAN);

          // Line end point (near label)
          const lineEndRadius = outerRadius + 18;
          const lineX2 = cx + lineEndRadius * Math.cos(-midAngle * RADIAN);
          const lineY2 = cy + lineEndRadius * Math.sin(-midAngle * RADIAN);

          const isLeftSide = x < cx;
          const displayName = name.length > 20 ? name.substring(0, 18) + '..' : name;
          const percentText = `${(percent * 100).toFixed(1)}%`;

          return (
            <g>
              {/* Leader line */}
              <path
                d={`M ${lineX1} ${lineY1} L ${lineX2} ${lineY2} L ${isLeftSide ? lineX2 - 8 : lineX2 + 8} ${lineY2}`}
                stroke="#94a3b8"
                strokeWidth={1}
                fill="none"
              />
              {/* Label text */}
              <text
                x={isLeftSide ? x - 5 : x + 5}
                y={y}
                fill="#f1f5f9"
                textAnchor={isLeftSide ? 'end' : 'start'}
                dominantBaseline="central"
                fontSize={11}
                fontWeight={500}
              >
                {displayName}
              </text>
              {/* Percentage below name */}
              <text
                x={isLeftSide ? x - 5 : x + 5}
                y={y + 12}
                fill="#94a3b8"
                textAnchor={isLeftSide ? 'end' : 'start'}
                dominantBaseline="central"
                fontSize={10}
              >
                {percentText} ({value.toLocaleString()})
              </text>
            </g>
          );
        };

        // Custom legend that shows full names with values
        const renderLegend = (props: any) => {
          const { payload } = props;
          return (
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2 px-2">
              {payload.map((entry: any, index: number) => (
                <div key={`legend-${index}`} className="flex items-center gap-1.5">
                  <div
                    className="w-3 h-3 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-xs text-slate-300 max-w-[150px] truncate" title={entry.value}>
                    {entry.value}
                  </span>
                </div>
              ))}
            </div>
          );
        };

        return (
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="42%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={85}
                innerRadius={0}
                fill="#8884d8"
                dataKey="value"
                paddingAngle={1}
              >
                {data.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                    stroke="#1e293b"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0];
                    const percent = ((item.value as number) / total * 100).toFixed(1);
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{item.name}</p>
                        <p className="text-slate-300 text-xs">
                          Value: <span className="text-white font-medium">{(item.value as number).toLocaleString()}</span>
                        </p>
                        <p className="text-slate-300 text-xs">
                          Percentage: <span className="text-white font-medium">{percent}%</span>
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend content={renderLegend} />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'grouped_bar':
        // Check data format: y_axis_list (wide format), group_by (long format), or fallback
        const yAxisList = visualization.y_axis_list;
        const groupBy = visualization.group_by;
        let groupedData: any[];
        let groupKeys: string[];

        if (yAxisList && yAxisList.length > 0) {
          // Wide format: Vendor | cancelled | expired | rejected
          groupedData = transformWideData(
            tableData,
            visualization.x_axis || tableData.columns[0],
            yAxisList
          );
          groupKeys = yAxisList;
        } else if (groupBy) {
          // Long format (pivot): Status | Contractor | Count → {name: "Contractor", Cancelled: X, Expired: Y, ...}
          const pivoted = pivotData(
            tableData,
            visualization.x_axis || tableData.columns[1],
            visualization.y_axis || tableData.columns[2],
            groupBy
          );
          groupedData = pivoted.data;
          groupKeys = pivoted.groupValues;
        } else {
          // Fallback: standard transformation with value/value2
          groupedData = data;
          groupKeys = [yAxisLabel, yAxisSecondaryLabel].filter(Boolean);
        }

        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={groupedData} margin={{ top: 20, right: 20, left: 10, bottom: 80 }}>
              <defs>
                {COLORS.map((color, i) => (
                  <linearGradient key={`gradient-${i}`} id={`groupedBarGradient${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={1} />
                    <stop offset="100%" stopColor={color} stopOpacity={0.7} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={90}
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickFormatter={(value) => value.length > 18 ? value.substring(0, 16) + '..' : value}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                width={50}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{label}</p>
                        {payload.map((entry: any, index: number) => (
                          <p key={index} className="text-slate-300 text-xs">
                            {entry.name}: <span style={{ color: COLORS[index % COLORS.length] }} className="font-medium">{(entry.value as number).toLocaleString()}</span>
                          </p>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              {(yAxisList && yAxisList.length > 0) || groupBy ? (
                // Render a bar for each column/group value (e.g., cancelled, expired, rejected)
                groupKeys.map((groupKey, index) => (
                  <Bar
                    key={groupKey}
                    dataKey={groupKey}
                    name={groupKey}
                    fill={`url(#groupedBarGradient${index % COLORS.length})`}
                    radius={[4, 4, 0, 0]}
                  />
                ))
              ) : (
                // Fallback: render value and value2 bars
                <>
                  <Bar dataKey="value" name={yAxisLabel} fill="url(#groupedBarGradient0)" radius={[4, 4, 0, 0]} />
                  {yAxisSecondaryLabel && (
                    <Bar dataKey="value2" name={yAxisSecondaryLabel} fill="url(#groupedBarGradient1)" radius={[4, 4, 0, 0]} />
                  )}
                </>
              )}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'horizontal_grouped_bar':
        // Horizontal grouped bar for many items (>10) - names readable on Y-axis
        const hYAxisList = visualization.y_axis_list;
        const hGroupBy = visualization.group_by;
        let hGroupedData: any[];
        let hGroupKeys: string[];

        if (hYAxisList && hYAxisList.length > 0) {
          // Wide format: Vendor | cancelled | expired | rejected
          hGroupedData = transformWideData(
            tableData,
            visualization.x_axis || tableData.columns[0],
            hYAxisList
          );
          hGroupKeys = hYAxisList;
        } else if (hGroupBy) {
          // Long format (pivot): Status | Contractor | Count
          const pivoted = pivotData(
            tableData,
            visualization.x_axis || tableData.columns[1],
            visualization.y_axis || tableData.columns[2],
            hGroupBy
          );
          hGroupedData = pivoted.data;
          hGroupKeys = pivoted.groupValues;
        } else {
          // Fallback: standard transformation with value/value2
          hGroupedData = data;
          hGroupKeys = [yAxisLabel, yAxisSecondaryLabel].filter(Boolean);
        }

        // Dynamic height: ~45px per row for grouped bars
        const hChartHeight = Math.min(800, Math.max(350, hGroupedData.length * 45));

        return (
          <ResponsiveContainer width="100%" height={hChartHeight}>
            <BarChart data={hGroupedData} layout="vertical" margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <defs>
                {COLORS.map((color, i) => (
                  <linearGradient key={`hgradient-${i}`} id={`hGroupedBarGradient${i}`} x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor={color} stopOpacity={0.7} />
                    <stop offset="100%" stopColor={color} stopOpacity={1} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} horizontal={false} />
              <XAxis
                type="number"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <YAxis
                dataKey="name"
                type="category"
                width={140}
                tick={{ fontSize: 11, fill: '#e2e8f0' }}
                tickFormatter={(value) => value.length > 22 ? value.substring(0, 20) + '..' : value}
                axisLine={{ stroke: '#475569' }}
                tickLine={{ stroke: '#475569' }}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-slate-800 p-3 border border-slate-600 rounded-lg shadow-xl">
                        <p className="font-semibold text-white text-sm mb-1">{label}</p>
                        {payload.map((entry: any, index: number) => (
                          <p key={index} className="text-slate-300 text-xs">
                            {entry.name}: <span style={{ color: COLORS[index % COLORS.length] }} className="font-medium">{(entry.value as number).toLocaleString()}</span>
                          </p>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '10px' }}
                formatter={(value) => <span className="text-slate-300 text-xs">{value}</span>}
              />
              {(hYAxisList && hYAxisList.length > 0) || hGroupBy ? (
                // Render a bar for each column/group value
                hGroupKeys.map((groupKey, index) => (
                  <Bar
                    key={groupKey}
                    dataKey={groupKey}
                    name={groupKey}
                    fill={`url(#hGroupedBarGradient${index % COLORS.length})`}
                    radius={[0, 4, 4, 0]}
                  />
                ))
              ) : (
                // Fallback: render value and value2 bars
                <>
                  <Bar dataKey="value" name={yAxisLabel} fill="url(#hGroupedBarGradient0)" radius={[0, 4, 4, 0]} />
                  {yAxisSecondaryLabel && (
                    <Bar dataKey="value2" name={yAxisSecondaryLabel} fill="url(#hGroupedBarGradient1)" radius={[0, 4, 4, 0]} />
                  )}
                </>
              )}
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="mt-4">
      {/* Toggle Button */}
      <div className="flex justify-end mb-2">
        <button
          onClick={() => setShowChart(!showChart)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
        >
          {showChart ? (
            <>
              <Table className="w-3.5 h-3.5" />
              Show Table
            </>
          ) : (
            <>
              <BarChart2 className="w-3.5 h-3.5" />
              Show Chart
            </>
          )}
        </button>
      </div>

      {/* Chart Container */}
      {showChart ? (
        <div className="bg-[#0f3460]/50 rounded-lg p-4 border border-indigo-500/20">
          {visualization.title && (
            <h3 className="text-sm font-medium text-slate-200 mb-4 text-center">
              {visualization.title}
            </h3>
          )}
          {renderChart()}
        </div>
      ) : (
        /* Table View */
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-[11px] border-collapse">
            <thead>
              <tr className="bg-indigo-500/20">
                {tableData.columns.map((col, i) => (
                  <th key={i} className="px-2 py-1.5 text-left text-indigo-300 font-semibold border border-indigo-500/20 whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.rows.slice(0, 50).map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-indigo-500/10">
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className="px-2 py-1 border border-indigo-500/10 text-slate-300">
                      {cell !== null ? String(cell) : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {tableData.rows.length > 50 && (
            <p className="text-[10px] text-slate-400 mt-2">
              Showing 50 of {tableData.rows.length} rows
            </p>
          )}
        </div>
      )}
    </div>
  );
}
