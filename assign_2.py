"""
Multi-Agent Trip Designer (clean version, no background image)
"""

from __future__ import annotations
import os
import asyncio
import time
from typing import Callable, Dict, List, Optional, Any

import streamlit as st
from dotenv import load_dotenv
from tavily import TavilyClient

# ──────────────────────────────────────────────────────────────
# Environment Setup
# ──────────────────────────────────────────────────────────────

load_dotenv()
os.environ.setdefault("OPENAI_LOG", "error")
os.environ.setdefault("OPENAI_TRACING", "false")

TOOL_LOGGER: Optional[Callable[[Dict[str, Any]], None]] = None


def set_tool_logger(logger: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    global TOOL_LOGGER
    TOOL_LOGGER = logger


def log_tool_event(event: Dict[str, Any]) -> None:
    if TOOL_LOGGER is not None:
        try:
            TOOL_LOGGER(event)
        except Exception:
            pass


def redact_for_logs(value: Any) -> Any:
    if isinstance(value, str):
        low = value.lower()
        if any(k in low for k in ("api_key", "token", "secret", "password")):
            return "[redacted]"
        return value if len(value) <= 300 else value[:120] + "… [truncated]"
    if isinstance(value, dict):
        return {k: ("[redacted]" if any(s in k.lower() for s in ("key", "token", "secret", "password"))
                    else redact_for_logs(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact_for_logs(v) for v in value]
    return value


# ──────────────────────────────────────────────────────────────
# Agent Framework Imports
# ──────────────────────────────────────────────────────────────

from agents import Agent, Runner, function_tool  # type: ignore


# ──────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────

@function_tool
def internet_search(query: str) -> str:
    """Internet search backed by Tavily."""
    log_tool_event({"type": "call", "tool": "internet_search", "args": {"query": redact_for_logs(query)}})

    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            msg = "missing TAVILY_API_KEY in environment."
            log_tool_event({"type": "error", "tool": "internet_search", "error": msg})
            return f"Search error: {msg}"

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=3)

        items = response.get("results", [])
        lines = [f"- {it.get('title', 'N/A')}: {it.get('content', 'N/A')}" for it in items]
        output = "\n".join(lines) if lines else "No results found."

        log_tool_event({
            "type": "result",
            "tool": "internet_search",
            "preview": redact_for_logs(output[:400] + ("…" if len(output) > 400 else "")),
        })
        return output

    except Exception as e:
        log_tool_event({"type": "error", "tool": "internet_search", "error": str(e)})
        return f"Search error: {e}"

    finally:
        log_tool_event({"type": "end", "tool": "internet_search"})


# ──────────────────────────────────────────────────────────────
# Agent Prompts
# ──────────────────────────────────────────────────────────────

VERIFIER_INSTRUCTIONS = """
You are a thoughtful travel reviewer and itinerary analyst.
Your mission is to evaluate the proposed travel plan, ensuring it’s smooth, practical, and inspiring.

Steps:
1. Cross-check all suggestions — destinations, hotels, attractions, and pacing.
2. Make sure the season, cost, and transitions between places make sense.
3. Rewrite and polish the plan in a friendly, imaginative, and natural tone.
4. Gently adjust or replace any unrealistic elements, explaining improvements.
5. Organize the final itinerary clearly, using days or themes for structure.

Goal: Deliver a refined, trustworthy, and motivating travel plan the user can truly rely on.
"""

DESIGNER_INSTRUCTIONS = """
You are a creative trip designer with a strong sense of adventure and style.
Build a personalized travel experience that blends exploration, culture, rest, and great food.

Guidelines:
- Think like a traveler who enjoys the journey, not a robot listing stops.
- Keep the user’s budget, duration, and interests central to your choices.
- Ensure a logical order with minimal travel time and healthy pacing.
- Use vivid descriptions (“Start your morning at a quiet seaside café…”).
- Present the plan in a clear structure organized by day or activity type.

Goal: Craft an itinerary that feels personal, balanced, and effortlessly exciting.
"""

verifier_agent = Agent(
    name="Verifier Agent",
    model="openai.gpt-4o",
    instructions=VERIFIER_INSTRUCTIONS.strip(),
    tools=[internet_search],
)

designer_agent = Agent(
    name="Designer Agent",
    model="openai.gpt-4o",
    instructions=DESIGNER_INSTRUCTIONS.strip(),
)


# ──────────────────────────────────────────────────────────────
# Async-safe Runner Helpers
# ──────────────────────────────────────────────────────────────

async def run_agent_async(agent: Agent, input_text: str):
    result = await Runner.run(agent, input_text)
    return getattr(result, "final_output", None) or getattr(result, "text", None) or str(result)


def run_agent(agent: Agent, text: str):
    """Runs agents safely even inside Streamlit's event loop."""
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(run_agent_async(agent, text))
    except RuntimeError:
        return asyncio.run(run_agent_async(agent, text))


# ──────────────────────────────────────────────────────────────
# Streamlit UI
# ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Trip Designer", page_icon="🧳", layout="centered")

st.title("🗺️ Multi-Agent Trip Designer")
st.caption("_Designer → Verifier: Crafting your perfect travel experience._")

# Sidebar controls
with st.sidebar:
    st.header("Session Tools")
    if st.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()

    st.subheader("Try these ideas")
    st.code("Design a 7-day Japan trip for a foodie traveler on a $2,000 budget")
    st.code("Weekend getaway to Iceland focused on relaxation and photography")

    show_tools = st.toggle("Display live tool events", value=True)
    if show_tools:
        with st.expander("🔧 Tool activity (live)", expanded=False):
            tool_panel = st.container()
    else:
        tool_panel = st.container()

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "meta" not in st.session_state:
    st.session_state.meta = []

# Render past chat
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and i < len(st.session_state.meta):
            st.caption(st.session_state.meta[i].get("trace", ""))

# Chat input
user_input = st.chat_input("Tell me where you’d like to go and what kind of experience you’re after.")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.meta.append(None)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        live_msg = st.empty()
        progress = st.progress(0)
        tool_events: List[Dict[str, Any]] = []

        def ui_tool_logger(event: Dict[str, Any]) -> None:
            tool_events.append(event)
            with tool_panel:
                st.markdown("**Recent tool activity**")
                for ev in tool_events[-60:]:
                    t, et = ev.get("tool", "unknown"), ev.get("type", "event")
                    if et == "call":
                        st.write(f"• **{t}** called with `{ev.get('args')}`")
                    elif et == "result":
                        st.write(f"• **{t}** result preview:\n\n> {ev.get('preview')}")
                    elif et == "error":
                        st.error(f"• **{t}** error: {ev.get('error')}")
                    elif et == "end":
                        st.write(f"• **{t}** finished")

        set_tool_logger(ui_tool_logger)

        try:
            live_msg.markdown("🧭 Designer Agent is curating your journey…")
            plan_text = run_agent(designer_agent, user_input)
            progress.progress(40)

            live_msg.markdown("🔍 Verifier Agent is reviewing and enhancing your itinerary…")
            review_text = run_agent(verifier_agent, plan_text)
            progress.progress(90)

            live_msg.markdown("✅ Done! Here’s your beautifully refined itinerary:")
            time.sleep(0.2)
            progress.progress(100)

            st.success("✨ **Final Trip Plan** (Verified and Ready to Go)")
            st.markdown(review_text)
            with st.expander("See original draft from Designer Agent"):
                st.markdown(plan_text)

            st.session_state.messages.append({"role": "assistant", "content": review_text})
            st.session_state.meta.append({"trace": "Designer Agent → Verifier Agent"})

        except Exception as e:
            live_msg.markdown("❌ Something went wrong.")
            err = f"⚠️ There was an error generating your plan:\n\n```\n{e}\n```"
            st.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
            st.session_state.meta.append({"trace": "Runtime error."})

        finally:
            set_tool_logger(None)
