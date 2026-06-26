import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    content: str


def search_web(query: str, *, max_results: int = 5) -> list[SearchResult]:
    """Search the web with Tavily and normalize the top results."""
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("Missing TAVILY_API_KEY")

    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        topic="general",
        search_depth="advanced",
        include_answer=False,
        include_raw_content=False,
        max_results=max_results,
    )

    results = response.get("results", [])
    normalized_results: list[SearchResult] = []
    for item in results:
        normalized_results.append(
            SearchResult(
                title=item.get("title", "Untitled result"),
                url=item.get("url", ""),
                content=item.get("content", "").strip(),
            )
        )

    return normalized_results


def format_search_context(results: list[SearchResult]) -> str:
    """Build compact context for the LLM prompt."""
    if not results:
        return "No web search results were returned."

    formatted_chunks: list[str] = []
    for index, result in enumerate(results, start=1):
        formatted_chunks.append(
            f"[{index}] {result.title}\nURL: {result.url}\nSummary: {result.content}"
        )

    return "\n\n".join(formatted_chunks)
