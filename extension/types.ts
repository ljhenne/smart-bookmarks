export interface PageContent {
  html: string;
  selectedText: string;
  text: string;
  /** ISO 8601 string of when the page was captured. */
  timestamp: string;
  title: string;
  url: string;
}

export interface ScriptPayload {
  html: string;
  selectedText: string;
  text: string;
  timestamp: string;
}

export interface SearchResult {
  category: string;
  /** ISO 8601 creation timestamp. */
  created_at: string;
  id: number;
  /** ISO 8601 timestamp of last processing run. */
  last_processed_at: string;
  /** Semantic similarity score relative to the query (0.0 to 1.0). */
  similarity: number;
  summary: string;
  tags: string[];
  title: string;
  url: string;
}

