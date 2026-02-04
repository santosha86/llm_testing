export interface TableData {
  columns: string[];
  rows: any[][];
}

export interface VisualizationConfig {
  should_visualize: boolean;
  chart_type: 'bar' | 'line' | 'pie' | 'horizontal_bar' | 'grouped_bar' | 'horizontal_grouped_bar' | null;
  x_axis: string | null;
  y_axis: string | null;
  y_axis_secondary?: string | null;
  y_axis_list?: string[] | null;  // For 3+ numeric columns (wide format data)
  group_by?: string | null;  // Column to group/pivot data by (for multi-category comparisons)
  title: string | null;
}

export interface DisambiguationOption {
  value: string;
  display: string;
  description?: string;
}

export interface ClarificationOption {
  value: string;
  label: string;
  description?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  originalQuery?: string; // Store original query for clarification resubmit
  metadata?: {
    responseTime: string;
    sources: string[];
    tableData?: TableData;
    sqlQuery?: string;
    needsDisambiguation?: boolean;
    disambiguationOptions?: DisambiguationOption[];
    needsClarification?: boolean;
    clarificationMessage?: string;
    clarificationOptions?: ClarificationOption[];
    visualization?: VisualizationConfig;
  };
}

export interface CategoryData {
  id: string;
  label: string;
  icon: any; // Lucide Icon type
  queries: string[];
}

export interface CardData {
  title: string;
  color: 'red' | 'orange' | 'green' | 'yellow' | 'pink' | 'purple' | 'blue' | 'teal';
  items: string[];
}

export interface RoadmapItem {
  feature: string;
  pocStatus: string;
  pocClass: 'red' | 'orange' | 'green';
  prodVision: string;
  prodClass: 'red' | 'orange' | 'green';
}