# Personal Research Assistant Agent

A minimal but *real* agentic AI project: an agent that searches the web,
reasons over the results, and answers your question with cited sources.

It's built directly on each provider's native tool-use (function calling)
API, so you can see exactly how the **Reason → Act → Observe** loop works —
no framework hiding the mechanics.

## How it works

1. You ask a question.
2. The model decides: "Do I need to search the web for this, or do I already know?"
3. If it needs info, it calls the `search_web` tool with a query.
4. Your code actually runs the search (via DuckDuckGo) and sends the results back to the model.
5. The model reads the results and decides: search again for more/different info, or answer now.
6. Once satisfied, it writes a final answer with a Sources list.

This loop (steps 2–5) is the core of every agent, from simple research bots
to complex coding agents — it's just **search + tools + a bigger loop**.

## Files in this project

| File | Provider | Model used | SDK |
| `research_agent.py` | Google Gemini | `gemini-2.5-flash` | `google-genai` |

Each has a matching `requirements*.txt` file. Only install and use **one**
version at a time unless you want to compare them.

## Setup

1. **Install Python 3.9+** if you don't have it.

2. **Get an API key** from whichever provider you want to use:
   - Gemini: https://aistudio.google.com/apikey (generous free tier, no billing needed to start)

3. **Install dependencies** for your chosen version:
   ```bash

   pip install -r requirements.txt      # Gemini
   ```

4. **Set your API key as an environment variable.**

   macOS / Linux (bash):
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export DEEPSEEK_API_KEY="sk-..."
   export GEMINI_API_KEY="..."
   ```

   Windows (PowerShell):
   ```powershell
   $env:ANTHROPIC_API_KEY="sk-ant-..."
   $env:DEEPSEEK_API_KEY="sk-..."
   $env:GEMINI_API_KEY="..."
   ```
   Note: `$env:` only sets the variable for the current terminal session. For
   a permanent setting on Windows, use `setx VAR_NAME "value"` and then open
   a **new** terminal window.

## Run it

```bash
python research_agent.py "What are the health effects of intermittent fasting?"

```



You'll see the agent's reasoning and tool calls printed live, followed by a
final answer with sources.

## How this differs from a normal "call the API, get an answer" project

| | Normal API project | This agent |
|---|---|---|
| **What it can do** | Generate text from memory only | Generate text *and* run a real tool (web search) |
| **Who decides what happens next** | Your code (fixed logic) | The model itself, based on what it reads |
| **Shape of the interaction** | One request → one response | A loop: reason → act → observe → repeat, up to `max_turns` times |
| **Can it get current information?** | No — limited to training data | Yes — it actually fetches live results and reasons over them |

The model isn't just answering — it's choosing whether to act, taking that
action, reading the result, and deciding whether to act again. That
decide → act → observe loop is what "agentic" actually means.

## Things to try next (in rough difficulty order)

1. **Add a second tool** — e.g. a `get_weather(city)` function, or a
   `read_webpage(url)` tool that fetches and returns the full text of a
   specific page (search only gives snippets). This teaches you how agents
   choose between *multiple* tools.
2. **Add memory** — save each Q&A pair to a JSON file, and let the agent
   check past research before searching again.
3. **Add a "critic" step** — after the agent drafts an answer, send it back
   to the model with a prompt like "Review this answer for accuracy and
   completeness before finalizing" — a simple form of self-reflection.
4. **Swap the CLI for a small web UI** — Flask or Streamlit, so you can ask
   questions in a browser instead of the terminal.
5. **Add source-limiting logic** — cap searches at 3 max to control cost,
   and log token usage per run.

## Why this design (a few notes for beginners)

- **No LangChain/AutoGPT.** You're calling each provider's API directly so
  you can see every message that goes back and forth. Once this makes
  sense, frameworks will feel like helpful shortcuts instead of black boxes.
- **`max_turns` is a safety valve.** Agents can loop forever if you let
  them; always cap the number of tool-call rounds.
- **Tool results go back as a message, formatted specially.** This trips
  people up at first:
  - Anthropic: a `tool_result` block inside a `user`-role message.
  - DeepSeek (OpenAI-style): a `role: "tool"` message matched by `tool_call_id`.
  - Gemini: a `function_response` part inside a `user`-role `Content` turn.

  Different shapes, same idea — feed the tool's output back into the
  conversation so the model can keep reasoning.

## Troubleshooting

- **`402 Insufficient Balance` (DeepSeek)** — your account has no prepaid
  credit. Top up at platform.deepseek.com; no code changes needed.
- **`export` not recognized (Windows)** — that's bash/macOS/Linux syntax.
  Use `$env:VAR_NAME="value"` in PowerShell instead.
- **`Invalid requirement` when installing** — usually means the
  `requirements*.txt` file got corrupted (e.g. a command got pasted into
  it by accident). Recreate the file with just the package lines shown
  above.
- **Rotate any API key you've pasted into a chat or terminal log**, just as
  good practice — regenerate it from the provider's dashboard once you're
  done testing.
