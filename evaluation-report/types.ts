/**
 * Type definitions for LLM Evaluation Report
 */

// Test result for a single evaluation
export interface TestResult {
  id: string;
  category: 'math' | 'logic' | 'reasoning' | 'long-context';
  question: string;
  expectedAnswer: string;
  baselineResponse: string;
  customerResponse: string;
  baselinePass: boolean;
  customerPass: boolean;
  baselineLatency: number; // in seconds
  customerLatency: number; // in seconds
  baselineTokens?: number;
  customerTokens?: number;
  failureReason?: string;
}

// Score summary for a category
export interface CategoryScore {
  category: string;
  baselineScore: number; // percentage
  customerScore: number; // percentage
  gap: number; // difference
  icon: string;
  totalTests: number;
  baselinePassed: number;
  customerPassed: number;
}

// Overall report data structure
export interface ReportData {
  // Metadata
  reportId: string;
  reportDate: string;
  reportTitle: string;

  // Providers being compared
  baselineProvider: string;
  customerProvider: string;

  // Overall scores
  overallBaseline: number;
  overallCustomer: number;

  // Category breakdown
  categoryScores: CategoryScore[];

  // Individual test results
  testResults: TestResult[];

  // Analysis
  criticalFailures: string[];
  recommendations: Recommendation[];

  // Performance metrics
  avgBaselineLatency: number;
  avgCustomerLatency: number;
  totalTestsRun: number;
  testDuration: number; // total time in seconds
}

export interface Recommendation {
  type: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  action?: string;
}

// API response format (for fetching report data)
export interface ReportAPIResponse {
  success: boolean;
  data?: ReportData;
  error?: string;
}

// Filter options for the report view
export interface ReportFilters {
  categories: string[];
  showPassedOnly: boolean;
  showFailedOnly: boolean;
  provider: 'baseline' | 'customer' | 'both';
}

// Export format options
export type ExportFormat = 'pdf' | 'json' | 'csv' | 'html';
