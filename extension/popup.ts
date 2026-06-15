import { PageContent, ScriptPayload } from './types.js';
import { saveBookmark, searchBookmarks } from './api.js';

// Cache for DOM elements to avoid repetitive query lookups
interface DOMElements {
  tabButtons: NodeListOf<HTMLButtonElement>;
  tabContents: NodeListOf<HTMLElement>;
  previewTitle: HTMLElement | null;
  previewUrl: HTMLElement | null;
  savePageBtn: HTMLButtonElement | null;
  saveBtnSpinner: HTMLElement | null;
  saveErrorMessage: HTMLElement | null;
  maggieSuccessNest: HTMLElement | null;
  searchInput: HTMLInputElement | null;
  searchBtn: HTMLElement | null;
  searchResults: HTMLElement | null;
}

let dom: DOMElements;
let pageData: PageContent | null = null;

/**
 * Utility to pause execution using async/await.
 * @param ms - Milliseconds to sleep.
 * @returns A promise that resolves after the specified duration.
 */
const sleep = (ms: number): Promise<void> => 
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Helper to safely extract hostname from a URL string.
 * @param urlString - The raw URL string.
 * @returns The extracted hostname, or the original URL string if invalid.
 */
function getDisplayUrl(urlString: string): string {
  try {
    return new URL(urlString).hostname;
  } catch {
    return urlString;
  }
}

/**
 * Safely escapes HTML characters in a string to prevent XSS.
 * @param str - The raw input string.
 * @returns The escaped, safe HTML string.
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize the DOM elements registry
  dom = {
    tabButtons: document.querySelectorAll(".tab-btn"),
    tabContents: document.querySelectorAll(".tab-content"),
    previewTitle: document.getElementById("preview-title"),
    previewUrl: document.getElementById("preview-url"),
    savePageBtn: document.getElementById("save-page-btn") as HTMLButtonElement | null,
    saveBtnSpinner: document.getElementById("save-btn-spinner"),
    saveErrorMessage: document.getElementById("save-error-message"),
    maggieSuccessNest: document.getElementById("maggie-success-nest"),
    searchInput: document.getElementById("search-input") as HTMLInputElement | null,
    searchBtn: document.getElementById("search-btn"),
    searchResults: document.getElementById("search-results"),
  };

  setupTabs();
  await initializePageData();
  setupSaveButton();
  setupSearchLogic();
});

/**
 * Initializes navigation event handlers for switching between the extension's tabs.
 * Attaches click listeners to all tab buttons to toggle active CSS styles and display
 * the corresponding tab content panel.
 */
function setupTabs() {
  dom.tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.getAttribute("data-tab");
      if (!targetTabId) return;

      dom.tabButtons.forEach((b) => b.classList.remove("active"));
      dom.tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(targetTabId)?.classList.add("active");
    });
  });
}

/**
 * Query the active browser tab, inject script to scrape content, and cache the page info.
 */
async function initializePageData() {
  try {
    const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!activeTab || !activeTab.id) {
      showSaveError("Could not retrieve active tab details.");
      return;
    }

    const { title = "Unknown Page", url = "" } = activeTab;

    if (dom.previewTitle) dom.previewTitle.textContent = title;
    if (dom.previewUrl) dom.previewUrl.textContent = getDisplayUrl(url);

    let html = "";
    let text = "";
    let selectedText = "";
    let timestamp = new Date().toISOString();

    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        func: (): ScriptPayload => ({
          html: document.documentElement.outerHTML,
          selectedText: window.getSelection()?.toString() || "",
          text: document.body?.innerText || "",
          timestamp: new Date().toISOString()
        })
      });

      if (results?.[0]?.result) {
        const payload = results[0].result as ScriptPayload;
        html = payload.html;
        text = payload.text;
        selectedText = payload.selectedText;
        timestamp = payload.timestamp;
      }
    } catch (err) {
      console.warn("Could not inject content script:", err);
    }

    pageData = {
      title,
      url,
      html,
      text,
      selectedText,
      timestamp
    };
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err);
    showSaveError(`Failed to load page info: ${errMsg}`);
  }
}

/**
 * Display errors related to saving bookmarks in the UI.
 * @param msg - The error message to display.
 */
function showSaveError(msg: string): void {
  if (dom.saveErrorMessage) {
    dom.saveErrorMessage.textContent = msg;
    dom.saveErrorMessage.classList.remove("hidden");
  }
}

/**
 * Configure behavior and event listeners for the "Save Bookmark" action.
 */
function setupSaveButton() {
  if (!dom.savePageBtn) return;

  dom.savePageBtn.addEventListener("click", async () => {
    if (!pageData) {
      showSaveError("Page data is not ready yet. Please try again.");
      return;
    }

    dom.savePageBtn!.disabled = true;
    dom.saveBtnSpinner?.classList.remove("hidden");
    const btnText = dom.savePageBtn!.querySelector(".btn-text");
    if (btnText) btnText.textContent = "Saving...";
    
    if (dom.saveErrorMessage) {
      dom.saveErrorMessage.textContent = "";
      dom.saveErrorMessage.classList.add("hidden");
    }

    const startTime = Date.now();

    try {
      await saveBookmark(pageData);

      const elapsed = Date.now() - startTime;
      const remainingDelay = Math.max(0, 600 - elapsed);
      if (remainingDelay > 0) {
        await sleep(remainingDelay);
      }

      dom.saveBtnSpinner?.classList.add("hidden");
      if (btnText) btnText.textContent = "Saved!";
      dom.savePageBtn!.classList.add("saved");
      dom.maggieSuccessNest?.classList.remove("hidden");
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      showSaveError(errMsg);
      
      dom.savePageBtn!.disabled = false;
      dom.saveBtnSpinner?.classList.add("hidden");
      if (btnText) btnText.textContent = "Save Bookmark";
    }
  });
}

/**
 * Configure behavior and search handlers for fetching and rendering search results securely.
 */
function setupSearchLogic() {
  const performSearch = async () => {
    if (!dom.searchInput || !dom.searchResults) return;
    const query = dom.searchInput.value.trim();
    if (!query) return;

    dom.searchResults.innerHTML = `
      <div class="search-loading-state">
        <div class="spinner"></div>
        <p>Searching bookmarks...</p>
      </div>
    `;

    try {
      const results = await searchBookmarks(query);

      if (results.length === 0) {
        dom.searchResults.innerHTML = `
          <div class="search-empty-state">
            <p>No matching bookmarks found</p>
          </div>
        `;
        return;
      }

      dom.searchResults.innerHTML = "";
      results.forEach((res) => {
        const item = document.createElement("div");
        item.className = "search-result-item";

        const scorePercent = Math.max(0, Math.min(100, Math.round(res.similarity * 100)));
        const displayUrl = getDisplayUrl(res.url);

        // Safely escape all variable content injected into the HTML to prevent DOM XSS
        const escapedTitle = escapeHtml(res.title || "Untitled Bookmark");
        const escapedSummary = escapeHtml(res.summary || "");
        const escapedCategory = escapeHtml(res.category || "General");
        const escapedUrl = escapeHtml(res.url || "");
        const escapedDisplayUrl = escapeHtml(displayUrl);

        item.innerHTML = `
          <div class="search-result-header">
            <span class="search-result-title" title="${escapedTitle}">${escapedTitle}</span>
            <span class="search-result-score">${scorePercent}%</span>
          </div>
          <p class="search-result-summary">${escapedSummary}</p>
          <div class="search-result-meta">
            <span class="search-result-category">${escapedCategory}</span>
            <a href="#" class="search-result-link" title="${escapedUrl}">${escapedDisplayUrl}</a>
          </div>
        `;

        const link = item.querySelector(".search-result-link");
        const openUrl = () => chrome.tabs.create({ url: res.url });
        
        link?.addEventListener("click", (e) => {
          e.preventDefault();
          openUrl();
        });
        
        const titleSpan = item.querySelector(".search-result-title") as HTMLElement | null;
        if (titleSpan) {
          titleSpan.style.cursor = "pointer";
          titleSpan.style.textDecoration = "underline";
          titleSpan.addEventListener("click", (e) => {
            e.preventDefault();
            openUrl();
          });
        }

        dom.searchResults!.appendChild(item);
      });
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      dom.searchResults.innerHTML = `
        <div class="search-error-state">
          <p>Search failed: ${escapeHtml(errMsg)}</p>
        </div>
      `;
    }
  };

  dom.searchBtn?.addEventListener("click", performSearch);
  dom.searchInput?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") performSearch();
  });
}
