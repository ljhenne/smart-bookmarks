from datetime import datetime

from pydantic import BaseModel, Field



class Bookmark(BaseModel):
    """
    The final Bookmark record to be saved to the database.
    Contains the original metadata as well as generated vectors.
    """

    id_: int = Field(alias="id")

    created_at: datetime | None = None
    last_processed_at: datetime | None = None

    category: str | None = None
    summary: str | None = None
    summary_embedding: list[float] | None = None
    tags: list[str] | None = None
    title: str | None = None
    type_: str | None = None
    url: str | None = None

    model_config = {"populate_by_name": True}


class PageAttributes(BaseModel):
    """
    Structured metadata extracted from the webpage content by the LLM.
    """

    category: str
    summary: str
    tags: list[str]
    type_: str


class PageContent(BaseModel):
    """
    Represents the payload received from the Chrome Extension.
    Contains the HTML and text content extracted from the active tab.
    """

    title: str
    url: str
    html: str
    text: str
    selectedText: str
    timestamp: str


class SearchResultBookmark(BaseModel):
    """
    Represents a search result returned from the vector database query.
    Includes the calculated similarity score.
    """

    id_: int = Field(alias="id")
    similarity: float

    created_at: datetime | None = None
    last_processed_at: datetime | None = None

    category: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    title: str | None = None
    type_: str | None = None
    url: str | None = None

    model_config = {"populate_by_name": True}
