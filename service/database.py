import os

from google.cloud.sql.connector import Connector
from models import Bookmark

# Global connector instance
connector = Connector()


def get_db_connection():
    """
    Establishes and returns a connection to the Cloud SQL PostgreSQL database.

    Uses the Cloud SQL Python Connector with the pg8000 driver. Requires the
    following environment variables to be set:
    - PROJECT_ID: The GCP project ID.
    - REGION: The GCP region of the Cloud SQL instance.
    - INSTANCE_NAME: The name of the Cloud SQL instance.
    - DB_USER: The database user name.
    - DB_PASSWORD: The database password.
    - DB_NAME: The target database name.

    Returns:
        pg8000.dbapi.Connection: A connection object to the PostgreSQL database.

    Raises:
        KeyError: If any of the required database environment variables are missing.
    """
    instance_connection_string = (
        f"{os.environ['PROJECT_ID']}:"
        f"{os.environ['REGION']}:"
        f"{os.environ['INSTANCE_NAME']}"
    )
    return connector.connect(
        instance_connection_string,
        "pg8000",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        db=os.environ["DB_NAME"],
    )


def store_bookmark_in_db(bookmark: Bookmark):
    """
    Inserts a Bookmark record into the database, or updates an existing
    record if a conflict occurs on the 'id' primary key.

    Stores the embedding vector utilizing pgvector format.

    Args:
        bookmark (Bookmark): The Bookmark object to insert or update.

    Raises:
        KeyError: If any of the required database environment variables are missing.
        Exception: If any error occurs during the database connection or query
            execution.
    """
    query = """
        INSERT INTO bookmark (
            id,
            created_at,
            last_processed_at,
            title,
            url,
            summary,
            category,
            type,
            tags,
            summary_embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
        ON CONFLICT (id) DO UPDATE SET
            last_processed_at = EXCLUDED.last_processed_at,
            title = EXCLUDED.title,
            summary = EXCLUDED.summary,
            category = EXCLUDED.category,
            type = EXCLUDED.type,
            tags = EXCLUDED.tags,
            summary_embedding = EXCLUDED.summary_embedding;
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                query,
                [
                    bookmark.id_,
                    bookmark.created_at,
                    bookmark.last_processed_at,
                    bookmark.title,
                    bookmark.url,
                    bookmark.summary,
                    bookmark.category,
                    bookmark.type_,
                    bookmark.tags,
                    str(bookmark.summary_embedding),
                ],
            )
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()


def search_bookmarks_in_db(query_embedding: list[float], limit: int = 5) -> list[dict]:
    """
    Queries the database for bookmarks with summaries semantically similar to the query
        vector.

    Utilizes pgvector's cosine distance operator (<=>).

    Args:
        query_embedding (list[float]):
            The 768-dimensional vector embedding of the search query.
        limit (int, optional):
            The maximum number of search results to return. Defaults to 5.

    Returns:
        list[dict]: A list of dictionaries representing the matching bookmarks, each
            containing the fields (id, created_at, last_processed_at, title, url,
            summary, category, type, tags) and their similarity score.

    Raises:
        KeyError: If any of the required database environment variables are missing.
        Exception: If any error occurs during the database connection or query
            execution.
    """
    query = """
        SELECT
            id,
            created_at,
            last_processed_at,
            title,
            url,
            summary,
            category,
            type,
            tags,
            (1 - (summary_embedding <=> %s::vector)) as similarity
        FROM bookmark
        ORDER BY summary_embedding <=> %s::vector
        LIMIT %s;
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                query,
                [str(query_embedding), str(query_embedding), limit],
            )
            columns = [col[0] for col in cur.description]
            results = []
            for row in cur.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        finally:
            cur.close()
    finally:
        conn.close()
