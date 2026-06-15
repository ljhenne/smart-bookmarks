import traceback

from google import genai
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy
from models import PageAttributes


async def extract_page_attributes(api_key: str, content: str) -> PageAttributes:
    """
    Uses the Antigravity Agent to analyze webpage content and extract
    structured metadata (summary, tags, category, and type).

    Args:
        content (str): The raw text or HTML content of the webpage to analyze.

    Returns:
        PageAttributes: A structured object containing the extracted page summary,
            tags, category, and type.
    """
    config = LocalAgentConfig(
        response_schema=PageAttributes, policies=[policy.allow_all()], api_key=api_key
    )

    # Prefer plain text over raw HTML; cap at 8000 chars to stay within token limits
    content_capped = content[:8000]

    prompt = (
        "You are an expert webpage metadata extractor.\n"
        "Analyze the webpage content below and extract the page attributes "
        "(summary, tags, category, and type). Use the finish tool to return the "
        "extracted attributes when you are done.\n"
        f"Webpage content:\n{content_capped}"
    )
    try:
        async with Agent(config) as agent:
            response = await agent.chat(prompt)
            raw_attributes = await response.structured_output()

            if not raw_attributes:
                raise ValueError(
                    "Failed to generate structured page attributes from LLM response."
                )

            return PageAttributes.model_validate(raw_attributes)
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"Error extracting attributes: {str(e)}")


def generate_embedding(api_key: str, text: str) -> list[float]:
    """
    Generates a 768-dimensional vector embedding for the given text
    using the Gemini Embedding API.

    Args:
        text (str): The input text to generate the vector embedding for.

    Returns:
        list[float]: A 768-dimensional float list representing the vector embedding.
    """
    try:
        genai_client = genai.Client(api_key=api_key)
        embed_response = genai_client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            config=genai.types.EmbedContentConfig(output_dimensionality=768),
        )
        if not embed_response.embeddings or len(embed_response.embeddings) == 0:
            raise ValueError("Embedding model returned an empty response.")

        embedding = embed_response.embeddings[0].values
        if not embedding:
            raise ValueError("Embedding values are empty or missing in the response.")
        return embedding
    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"Error generating embedding: {str(e)}")
