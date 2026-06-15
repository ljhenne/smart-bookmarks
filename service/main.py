import hashlib
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from ai import extract_page_attributes, generate_embedding
from anyio import to_thread
from database import search_bookmarks_in_db, store_bookmark_in_db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Bookmark, PageContent, SearchResultBookmark

app = FastAPI(title="Smart Bookmarks Processor Service")

# Allow cross-origin requests from the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Asynchronous context manager to manage application startup and shutdown lifecycle.

    Args:
        _: The FastAPI application instance. Not used.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    print("[smart-bookmarks] Service started. Listening on http://localhost:8080")
    yield


def generate_id_from_url(url: str) -> int:
    """
    Helper to generate a deterministic integer ID from a URL.

    Args:
        url (str): The URL string to generate the ID for.

    Returns:
        int: A deterministic integer representation of the URL generated using SHA-256.
    """
    return int(hashlib.sha256(url.encode("utf-8")).hexdigest()[:8], 16)


@app.post("/process", response_model=Bookmark)
async def process_page_content(payload: PageContent):
    """
    Processes the page content payload, calls the LLM for metadata,
    generates an embedding, and stores it in the database.

    Args:
        payload (PageContent): The page content data payload containing url, html,
            text, title, and timestamp.

    Returns:
        Bookmark: The assembled and stored Bookmark object.

    Raises:
        HTTPException:
            - 400 Bad Request: If the timestamp in payload is invalid.
            - 500 Internal Server Error: If the LLM extraction fails,
              embedding generation fails, or a database error occurs.
    """
    print(
        f"[smart-bookmarks] POST /process received — url={payload.url!r} "
        f"html_len={len(payload.html)} text_len={len(payload.text)}"
    )
    try:
        ts_str = payload.timestamp.replace("Z", "+00:00")
        created_at = datetime.fromisoformat(ts_str)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid timestamp format in payload: {e}"
        )

    last_processed_at = datetime.now(timezone.utc)

    print("[smart-bookmarks] Calling LLM to extract page attributes...")
    try:
        content = payload.text or payload.html
        api_key = os.environ["GEMINI_API_KEY"]
        attributes = await extract_page_attributes(api_key, content)
        print(f"[smart-bookmarks] Parsed PageAttributes: {attributes!r}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error extracting page attributes: {str(e)}"
        )

    print("[smart-bookmarks] Generating embedding for summary...")
    try:
        embedding = generate_embedding(api_key, attributes.summary)
        print(f"[smart-bookmarks] Embedding generated — vector length={len(embedding)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating embedding: {str(e)}"
        )

    bookmark = Bookmark(
        created_at=created_at,
        last_processed_at=last_processed_at,
        id_=generate_id_from_url(payload.url),
        summary=attributes.summary,
        summary_embedding=embedding,
        tags=attributes.tags,
        category=attributes.category,
        type_=attributes.type_,
        title=payload.title,
        url=payload.url,
    )

    print(
        "[smart-bookmarks] Bookmark created successfully — "
        f"id={bookmark.id_} url={bookmark.url!r}"
    )

    print("[smart-bookmarks] Storing bookmark in database...")
    try:
        await to_thread.run_sync(store_bookmark_in_db, bookmark)
        print("[smart-bookmarks] Bookmark stored successfully in database.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return bookmark


@app.get("/search", response_model=list[SearchResultBookmark])
async def search_bookmarks(q: str, limit: int = 5):
    """
    Searches the db for bookmarks with summaries semantically similar to the query.

    Args:
        q (str): The search query text.
        limit (int, optional): Max search results to return. Defaults to 5.

    Returns:
        list[SearchResultBookmark]:
            A list of matching bookmarks with similarity scores.

    Raises:
        HTTPException:
            - 500 Internal Server Error: If embedding generation fails or
              database search fails.
    """
    print(f"[smart-bookmarks] GET /search received — query={q!r}")

    print("[smart-bookmarks] Generating embedding for query...")
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        query_embedding = generate_embedding(api_key, q)
        print(
            "[smart-bookmarks] Query embedding generated — "
            f"vector length={len(query_embedding)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating query embedding: {str(e)}"
        )

    print("[smart-bookmarks] Querying database for similar bookmarks...")
    try:
        results = await to_thread.run_sync(
            search_bookmarks_in_db, query_embedding, limit
        )
        print(f"[smart-bookmarks] Found {len(results)} matching bookmarks.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database search error: {str(e)}")

    print("[smart-bookmarks] Formatting and returning search results.")
    search_results = []
    for row in results:
        search_results.append(
            SearchResultBookmark(
                id_=row["id"],
                created_at=row["created_at"],
                last_processed_at=row["last_processed_at"],
                title=row["title"],
                url=row["url"],
                summary=row["summary"],
                category=row["category"],
                type_=row["type"],
                tags=row["tags"],
                similarity=float(row["similarity"]),
            )
        )

    return search_results
