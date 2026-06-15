import { PageContent, SearchResult } from './types.js';

let apiBaseUrl: string | null = null;

/**
 * Retrieves the API base URL from the local config.json file.
 * 
 * @returns A promise that resolves to the API base URL string.
 */
async function getApiBaseUrl(): Promise<string> {
  if (apiBaseUrl) return apiBaseUrl;
  
  const response = await fetch(chrome.runtime.getURL('config.json'));
  if (!response.ok) {
    throw new Error(`Failed to load config.json: ${response.statusText}`);
  }
  const config = await response.json();
  apiBaseUrl = config.API_BASE_URL;
  return apiBaseUrl!;
}

/**
 * Saves a bookmark by sending the page content to the backend processor.
 * 
 * @param pageData - The parsed page elements and content to store.
 * @returns A promise that resolves when the page is successfully saved.
 * @throws An error if the server returns a non-OK status.
 */
export async function saveBookmark(pageData: PageContent): Promise<void> {
  const baseUrl = await getApiBaseUrl();
  const response = await fetch(`${baseUrl}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pageData),
  });

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
  }
}

/**
 * Searches for bookmarks semantically similar to the provided query.
 * 
 * @param query - The semantic search string.
 * @param limit - The maximum number of search results to retrieve (default: 3).
 * @returns A list of SearchResult matches.
 * @throws An error if the network request fails or returns a non-OK status.
 */
export async function searchBookmarks(query: string, limit: number = 3): Promise<SearchResult[]> {
  const baseUrl = await getApiBaseUrl();
  const response = await fetch(
    `${baseUrl}/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
  }

  return (await response.json()) as SearchResult[];
}

