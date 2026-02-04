import {
  AlertTriangle,
  BarChart2,
  Clock,
  Database,
  FileText,
  Lightbulb,
  MessageSquare,
  PieChart,
  Search,
  TrendingUp,
  Truck,
  Users
} from 'lucide-react';
import { CardData, CategoryData, RoadmapItem } from './types';

// API Configuration - use environment variable or fallback to ngrok URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://localhost:8000';

// Mock Responses for the demo
export const MOCK_RESPONSES: Record<string, string> = {
  "Which contractor caused most delays?": "Based on the analysis of Q3 data, **LogiTrans Corp** accounts for **32%** of all reported delays, primarily due to vehicle breakdown issues on the Northern Route.",
  "Why was Waybill 784 late?": "**Waybill 784** was delayed by **45 minutes**. The root cause was identified as *Wait for Load* at the distribution center. The driver arrived at 08:00, but loading commenced at 08:45.",
  "Summarize today's delayed dispatches": "Today, there are **14 delayed dispatches**. \n\n*   **Top Reason:** Traffic Congestion (8)\n*   **Secondary:** Documentation Issues (4)\n*   **Other:** Mechanical (2)\n\nAverage delay time: 22 minutes.",
  "Show me pending reconciliations": "There are currently **23 pending reconciliations** awaiting approval.\n\n*   **Operations:** 12\n*   **Finance:** 8\n*   **Disputes:** 3\n\nMost are aged < 48 hours.",
  "Top 5 delay reasons this week": "**Top 5 Delay Reasons (Current Week):**\n1.  Traffic / Route Congestion (35%)\n2.  Loading Dock Wait Time (22%)\n3.  Driver Unavailability (15%)\n4.  Documentation Errors (12%)\n5.  Vehicle Breakdown (10%)",
  "Compare contractor performance Q3": "**Q3 Performance Summary:**\n\n*   **FastTrack Logistics:** 98% On-Time (Top Performer)\n*   **Global Freight:** 92% On-Time\n*   **LogiTrans Corp:** 85% On-Time (Requires Review)\n\nFastTrack has improved efficiency by 5% since Q2."
};

export const VALUE_ADDED_CARDS: CardData[] = [
  {
    title: "📋 1. Problem Statement",
    color: "red",
    items: [
      "Business users depend heavily on analysts for reports",
      "Dispatch data is manually filtered and analyzed in Excel",
      "Operational questions take time to answer",
      "Non-technical users lack direct insight access",
      "High reporting workload slows decision-making"
    ]
  },
  {
    title: "🎯 2. Objective",
    color: "orange",
    items: [
      "Enable users to ask questions in natural language",
      "Provide instant access to dispatch insights",
      "Reduce dependency on analysts for queries",
      "Deliver fast, Data-Driven explanations and summaries",
      "Support both English and Arabic queries"
    ]
  },
  {
    title: "📊 3. Use Case Scope",
    color: "green",
    items: [
      "Ask questions using data (structure and non-structure)",
      "View details of waybills, contractors, and routes",
      "Check how contractors are performing",
      "Get short summaries of daily and weekly operations",
      "Get clear, easy-to-read summaries for managers"
    ]
  },
  {
    title: "💡 4. Value Added",
    color: "yellow",
    items: [
      "Self-service insights for business users",
      "50–60% reduction in report turnaround time",
      "Real-time operational visibility",
      "Faster, data-driven decision-making",
      "Improved transparency across teams",
      "Reduced analyst workload by 20–30%"
    ]
  },
  {
    title: "📈 5. Data Sources",
    color: "pink",
    items: [
      "Dispatch and operations data from SQL systems",
      "Waybill and operational documents (PDF files)",
      "Supporting data maintained in Excel files",
      "Contractor and route-related information",
      "Historical records used for summaries and comparisons"
    ]
  },
  {
    title: "🔍 6. Sample Queries",
    color: "purple",
    items: [
      "Which contractor has the most waybills assigned?",
      "Which contractor has the highest number of cancellations?",
      "What is the current status of waybill number 234?",
      "Show details of waybill number 234 (route and contractor).",
      "Show all waybills assigned to a selected contractor."
    ]
  },
  {
    title: "📊 7. Target Performance",
    color: "blue",
    items: [] // Special handling in component
  },
  {
    title: "🚀 8. Next Phase (Future Enhancements)",
    color: "teal",
    items: [
      "Integration with internal systems and data sources",
      "Enable near real-time data updates",
      "Integrate with Microsoft Teams and WhatsApp",
      "Control access based on user roles",
      "Allow voice-based questions",
      "Support multiple languages"
    ]
  }
];

export const ROADMAP_DATA: RoadmapItem[] = [
  { feature: "🎯 Answer Accuracy", pocStatus: "70%", pocClass: "green", prodVision: "90%+", prodClass: "green" },
  { feature: "📊 Data Sources", pocStatus: "Limited", pocClass: "orange", prodVision: "Full Data", prodClass: "green" },
  { feature: "🌐 Languages", pocStatus: "English & Arabic", pocClass: "green", prodVision: "English & Arabic", prodClass: "green" },
  { feature: "💬 Integration", pocStatus: "Basic", pocClass: "orange", prodVision: "Advanced", prodClass: "green" },
  { feature: "📈 Data-Driven Insights", pocStatus: "Basic", pocClass: "orange", prodVision: "Advanced", prodClass: "green" },
  { feature: "🖥️ Infrastructure", pocStatus: "Local Machine", pocClass: "orange", prodVision: "Secure, scalable environment", prodClass: "green" },
  { feature: "🔒 Governance", pocStatus: "No", pocClass: "red", prodVision: "Yes", prodClass: "green" },
  { feature: "⚙️ MLOps Automation", pocStatus: "No", pocClass: "red", prodVision: "Yes", prodClass: "green" },
  { feature: "🤖 Operational Intelligence", pocStatus: "No", pocClass: "red", prodVision: "Yes", prodClass: "green" },
  { feature: "*", pocStatus: "", pocClass: "green", prodVision: "The accuracy depends on data quality, completeness, and availability", prodClass: "green" },
];

// Fixed queries - must match FIXED_QUERIES keys in backend/fixed_queries.py
export const FIXED_QUERIES = {
  // Operations
  "Show today's dispatch details": true,
  "List all active dispatches": true,
  // Waybills
  "What is the current status of waybill 2-25-0010405?": true,
  "Show details of waybill 2-25-0010405": true,
  // Contractors
  "Which waybills are assigned to ALHBBAS FOR TRADING, TRANSPORT?": true,
  "Show contractor-wise waybill list": true,
  // Routes
  "Show the route details for waybill 2-25-0010405": true,
  "List all waybills on Route 45": true,
};

export const QUERY_CATEGORIES: CategoryData[] = [
  {
    id: "ops",
    label: "Operations",
    icon: Truck,
    queries: [
      "Show today's dispatch details",
      "List all active dispatches"
    ]
  },
  {
    id: "waybills",
    label: "Waybills",
    icon: FileText,
    queries: [
      "What is the current status of waybill 2-25-0010405?",
      "Show details of waybill 2-25-0010405"
    ]
  },
  {
    id: "contractors",
    label: "Contractors",
    icon: Users,
    queries: [
      "Which waybills are assigned to ALHBBAS FOR TRADING, TRANSPORT?",
      "Show contractor-wise waybill list"
    ]
  },
  {
    id: "routes",
    label: "Routes",
    icon: TrendingUp,
    queries: [
      "Show the route details for waybill 2-25-0010405",
      "List all waybills on Route 45"
    ]
  }
];

export const COLOR_MAP = {
  red: { border: 'border-l-red-400', shadow: 'shadow-red-500/10', title: 'text-red-400', bg: 'bg-red-500/5' },
  orange: { border: 'border-l-orange-400', shadow: 'shadow-orange-500/10', title: 'text-orange-400', bg: 'bg-orange-500/5' },
  green: { border: 'border-l-green-400', shadow: 'shadow-green-500/10', title: 'text-green-400', bg: 'bg-green-500/5' },
  yellow: { border: 'border-l-yellow-400', shadow: 'shadow-yellow-500/10', title: 'text-yellow-400', bg: 'bg-yellow-500/5' },
  pink: { border: 'border-l-pink-400', shadow: 'shadow-pink-500/10', title: 'text-pink-400', bg: 'bg-pink-500/5' },
  purple: { border: 'border-l-purple-400', shadow: 'shadow-purple-500/10', title: 'text-purple-400', bg: 'bg-purple-500/5' },
  blue: { border: 'border-l-blue-400', shadow: 'shadow-blue-500/10', title: 'text-blue-400', bg: 'bg-blue-500/5' },
  teal: { border: 'border-l-teal-400', shadow: 'shadow-teal-500/10', title: 'text-teal-400', bg: 'bg-teal-500/5' },
};
