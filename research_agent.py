"""
Personal Research Assistant Agent (Gemini version)
------------------------------------------------------
A minimal agentic AI example using Google's Gemini API.

Give it a question, and it will:
  1. Decide whether it needs to search the web
  2. Call a search tool if needed
  3. Read the results
  4. Decide whether it needs to search again (for follow-up info)
  5. Write a final answer with sources

Run:
    python research_agent_gemini.py "What caused the 2008 financial crisis?"
"""

import os
import sys
from google import genai
from google.genai import types
from ddgs import DDGS

# ---------------------------------------------------------------------------
# 1. THE TOOL
# ---------------------------------------------------------------------------
# An agent is just an LLM + tools + a loop. This is our only tool: web search.

def search_web(query: str, max_results: int = 5) -> str:
    """Search the web and return formatted snippets with sources."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found."

    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"[{i}] {r.get('title', 'No title')}\n"
            f"URL: {r.get('href', 'N/A')}\n"
            f"Snippet: {r.get('body', 'N/A')}\n"
        )
    return "\n".join(formatted)


# Gemini describes tools as "function declarations" grouped inside a Tool
# object. The schema shape matches OpenAPI, similar in spirit to the others.
SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_web",
            description=(
                "Search the web for current information. Use this whenever "
                "you need facts, recent events, statistics, or anything "
                "you're not fully certain about. Call it multiple times "
                "with different queries if one search isn't enough."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(
                        type="STRING",
                        description="The search query to run.",
                    )
                },
                required=["query"],
            ),
        )
    ]
)

SYSTEM_PROMPT = """You are a careful research assistant.

When the user asks a question:
- Use the search_web tool to gather information before answering. Don't rely on memory for anything time-sensitive or factual that you could verify.
- You may search multiple times with different queries to cover different angles of the question.
- Once you have enough information, write a clear, well-organized final answer.
- Always end your final answer with a "Sources" section listing the URLs you actually used, numbered to match your citations in the text (e.g. "solar prices fell sharply in 2024 [2]").
- If search results conflict or are inconclusive, say so honestly rather than guessing.
"""


# ---------------------------------------------------------------------------
# 2. THE AGENT LOOP
# ---------------------------------------------------------------------------
# This is the core of "agentic AI": Reason -> Act -> Observe -> repeat.

def run_agent(question: str, max_turns: int = 6, verbose: bool = True) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[SEARCH_TOOL],
    )

    # Gemini's history is a list of "Content" objects, each with a role
    # and one or more "parts" (text, function calls, or function results).
    contents = [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]

    for turn in range(max_turns):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)  # add model's turn to history

        function_calls = [
            part.function_call
            for part in candidate.content.parts
            if part.function_call is not None
        ]

        if function_calls:
            response_parts = []

            for call in function_calls:
                if call.name == "search_web":
                    query = call.args["query"]

                    if verbose:
                        text_parts = [
                            p.text for p in candidate.content.parts if p.text
                        ]
                        if text_parts:
                            print(f"\n[Gemini's reasoning] {' '.join(text_parts)}\n")
                        print(f"[Tool call] search_web(query={query!r})")

                    result = search_web(query)

                    if verbose:
                        preview = result[:300].replace("\n", " ")
                        print(f"[Tool result] {preview}...\n")

                    response_parts.append(
                        types.Part.from_function_response(
                            name="search_web",
                            response={"result": result},
                        )
                    )

            # Tool results go back as a "user"-role turn containing
            # function_response parts.
            contents.append(types.Content(role="user", parts=response_parts))

        else:
            # No function call -- the model is done, this is the final answer.
            return candidate.content.parts[0].text

    return "Reached max turns without a final answer. Try increasing max_turns."


# ---------------------------------------------------------------------------
# 3. CLI ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: set the GEMINI_API_KEY environment variable first.")
        print('  $env:GEMINI_API_KEY="your-key-here"   (PowerShell)')
        print('  export GEMINI_API_KEY="your-key-here" (bash/mac/linux)')
        sys.exit(1)

    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
    else:
        user_question = input("Ask a research question: ")

    print(f"\n{'='*60}\nQUESTION: {user_question}\n{'='*60}")

    answer = run_agent(user_question)

    print(f"\n{'='*60}\nFINAL ANSWER\n{'='*60}\n{answer}\n")