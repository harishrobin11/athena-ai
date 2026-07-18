"""
Athena AI - Unified Agent Execution Engine
Module: app.agents.agent_executor
Description: Manages multi-path intent routing, synchronous/streaming tool completion, 
             and provides dynamic context injection for live system time and cross-chat memory.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from .planner import create_plan
from ..tools.registry import execute_tool
from ..providers.ollama_provider import ask_llm, stream_llm
from ..core.agent_prompt import AGENT_PROMPT
from .router import classify_query


def gather_global_context(user_id: Optional[int], user_query: str) -> str:
    """
    Assembles real-time system clock values and queries long-term global cross-chat 
    semantic memory records, falling back to a direct SQL metadata scanner if empty.
    """
    current_time_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M:%S %p")
    context = f"Current System Timestamp: {current_time_str}\n"
    
    combined_memories = []
    seen = set()
    
    if user_id:
        # Pass 1: Attempt Semantic Memory Tool Registry Lookups
        try:
            memories_topic = execute_tool("search_memory", user_query, context={"user_id": user_id})
            memories_profile = execute_tool("search_memory", "User profile name identity deadline", context={"user_id": user_id})
            
            for mem in [memories_topic, memories_profile]:
                if mem and "No relevant information" not in str(mem):
                    for line in str(mem).split("\n"):
                        clean_line = line.strip()
                        if clean_line and "ended without a response" not in clean_line.lower():
                            combined_memories.append(clean_line)
                            seen.add(clean_line)
        except Exception as e:
            print(f"[CONTEXT LOG] Semantic memory tool pass skipped: {e}")

        # Pass 2: High-Durability Direct PostgreSQL Structural Scanner Fallback
        # If semantic extraction missed it, we scan actual message rows for explicit declarations
        if not combined_memories:
            try:
                from ..memory.database import list_conversations, get_messages
                
                # Fetch all historical chat frames owned by the active user context
                conversations = list_conversations(user_id)
                for conv in conversations:
                    conv_id = conv[0]
                    # Read all text entries in the target thread
                    messages = get_messages(conv_id)
                    for role, content in messages:
                        if role == "user":
                            content_lower = content.lower()
                            # Pinpoint clear biographical or project timeline declarations
                            if "my name is" in content_lower or "deadline is" in content_lower or "project deadline" in content_lower:
                                # Clean up formatting artifacts
                                clean_fact = content.strip().replace("\n", " ")
                                if clean_fact not in seen:
                                    combined_memories.append(f"Fact from past chat: '{clean_fact}'")
                                    seen.add(clean_fact)
            except Exception as db_err:
                print(f"[CONTEXT CRITICAL] Direct database scanner fallback failed: {db_err}")

    # Inject compiled historical facts back into the agent system payload
    if combined_memories:
        context += "\n[Long-Term Global Profile & Facts Recalled From Past Chats]:\n"
        context += "\n".join(combined_memories) + "\n"
        print("======== MEMORY INJECTED ========\n", context)
            
    return context


def run_agent(
    user_query: str,
    user_id: Optional[int] = None,
    selected_documents: Optional[List[str]] = None,
    image_path: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> str:
    """
    Executes a blocking, synchronous multi-turn agent evaluation frame.
    """
    print("===== AGENT (SYNCHRONOUS EXECUTION) =====")
    print("QUERY:", user_query)
    
    # 1. Harvest live clock properties and background long-term context profiles
    global_context = gather_global_context(user_id, user_query)
    route = classify_query(user_query, selected_documents)
    print(f"Route Selected: {route}")

    # Determine execution strategy
    if image_path is not None:
        plan = [{"tool": "analyze_image", "input": user_query}]
    else:
        if route == "chat":
            print("Fast path -> Direct LLM with Context")
            messages = [{"role": "system", "content": f"{AGENT_PROMPT}\n\n{global_context}"}]
            if history:
                for turn in history:
                    messages.append({"role": turn.get("role"), "content": turn.get("content")})
            messages.append({"role": "user", "content": user_query})
            return ask_llm(messages)
        elif route == "memory":
            plan = [{"tool": "search_memory", "input": user_query}]
        elif route == "documents":
            plan = [{"tool": "search_documents", "input": user_query}]
        elif route == "calculator":
            plan = [{"tool": "calculator", "input": user_query}]
        else:
            print("Planner required")
            plan = create_plan(user_query)

    if not plan:
        messages = [{"role": "system", "content": f"{AGENT_PROMPT}\n\n{global_context}"}]
        if history:
            for turn in history:
                messages.append({"role": turn.get("role"), "content": turn.get("content")})
        messages.append({"role": "user", "content": user_query})
        return ask_llm(messages)

    # Execute designated planning tools
    tool_context = {
        "user_id": user_id,
        "selected_documents": selected_documents,
        "image_path": image_path,
    }
    tool_outputs = []
    
    for step in plan:
        tool_name = step.get("tool")
        tool_input = step.get("input")
        print(f"Running Tool: {tool_name}")
        try:
            start_tool = time.time()
            result = execute_tool(tool_name=tool_name, tool_input=tool_input, context=tool_context)
            print(f"Tool completed in: {time.time() - start_tool:.2f} seconds")
            tool_outputs.append({"tool": tool_name, "success": True, "result": result})
        except Exception as e:
            print(f"Tool Error: {e}")
            tool_outputs.append({"tool": tool_name, "success": False, "result": str(e)})

    # Fast path return layer for non-streaming vision tasks
    if image_path is not None and tool_outputs:
        return tool_outputs[0]["result"]

    # Assemble unstructured text from tool strings
    tool_results = ""
    for output in tool_outputs:
        tool_results += f"\nTool: {output['tool']}\nSuccess: {output['success']}\nResult: {output['result']}\n"

    # Reconstruct single-session conversational log strings
    history_context_str = ""
    if history:
        for turn in history:
            role = "User" if turn.get("role") == "user" else "Assistant"
            history_context_str += f"{role}: {turn.get('content')}\n"

    prompt = f"""
    {AGENT_PROMPT}
    
    [GLOBAL ENVIRONMENT DETAILS]
    {global_context}
    
    [CONVERSATION HISTORY (CURRENT SESSION)]
    {history_context_str}
    
    User Question:
    {user_query}
    
    [AVAILABLE EXTRACTED TOOL DATA]
    {tool_results}
    
    Instructions:
    - Synthesize global environment details, history context, and tool properties cleanly.
    - Maintain absolute factual consistency with all stated long-term cross-chat memories.
    """
    
    print("Forwarding structural prompt payload to LLM...")
    return ask_llm([{"role": "user", "content": prompt}])


def run_agent_stream(
    user_query: str,
    user_id: Optional[int] = None,
    selected_documents: Optional[List[str]] = None,
    image_path: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    **kwargs
):
    """
    Executes a high-throughput, generative agent validation loop emitting token generators.
    """
    print("===== AGENT (STREAMING EXECUTION) =====")
    print("QUERY:", user_query)
    
    # 1. Harvest live clock properties and background long-term context profiles
    global_context = gather_global_context(user_id, user_query)
    route = classify_query(user_query, selected_documents)
    print(f"Route Selected: {route}")

    if image_path is not None:
        print("Image asset parameters detected.")
        plan = [{"tool": "analyze_image", "input": user_query}]
    else:
        if route == "chat":
            print("Fast path -> Direct Streaming completion loop initiated...")
            messages = [{"role": "system", "content": f"{AGENT_PROMPT}\n\n{global_context}"}]
            if history:
                for turn in history:
                    messages.append({"role": turn.get("role"), "content": turn.get("content")})
            messages.append({"role": "user", "content": user_query})
            return stream_llm(messages)
        elif route == "memory":
            plan = [{"tool": "search_memory", "input": user_query}]
        elif route == "documents":
            plan = [{"tool": "search_documents", "input": user_query}]
        elif route == "calculator":
            plan = [{"tool": "calculator", "input": user_query}]
        else:
            print("Planner required")
            plan = create_plan(user_query)

    if not plan:
        messages = [{"role": "system", "content": f"{AGENT_PROMPT}\n\n{global_context}"}]
        if history:
            for turn in history:
                messages.append({"role": turn.get("role"), "content": turn.get("content")})
        messages.append({"role": "user", "content": user_query})
        return stream_llm(messages)

    # Execute designated planning tools
    tool_context = {
        "user_id": user_id,
        "selected_documents": selected_documents,
        "image_path": image_path,
    }
    tool_outputs = []
    
    for step in plan:
        tool_name = step.get("tool")
        tool_input = step.get("input")
        try:
            start_tool = time.time()
            result = execute_tool(tool_name=tool_name, tool_input=tool_input, context=tool_context)
            tool_outputs.append({"tool": tool_name, "success": True, "result": result})
        except Exception as e:
            tool_outputs.append({"tool": tool_name, "success": False, "result": str(e)})

    # Fast path helper generator for streaming vision queries
    if image_path is not None and tool_outputs:
        result = tool_outputs[0]["result"]
        yield "" if result is None else str(result)
        return

    # Compile structured data elements
    tool_results = ""
    for output in tool_outputs:
        tool_results += f"\nTool: {output['tool']}\nSuccess: {output['success']}\nResult: {output['result']}\n"

    # Reconstruct single-session conversational logs
    history_context_str = ""
    if history:
        for turn in history:
            role = "User" if turn.get("role") == "user" else "Assistant"
            history_context_str += f"{role}: {turn.get('content')}\n"

    prompt = f"""
    {AGENT_PROMPT}
    
    [GLOBAL ENVIRONMENT DETAILS]
    {global_context}
    
    [CONVERSATION HISTORY (CURRENT SESSION)]
    {history_context_str}
    
    User Question:
    {user_query}
    
    [AVAILABLE EXTRACTED TOOL DATA]
    {tool_results}
    
    Instructions:
    - Synthesize global environment details, history context, and tool properties cleanly.
    - Maintain absolute factual consistency with all stated long-term cross-chat memories.
    """

    for chunk in stream_llm([{"role": "user", "content": prompt}]):
        yield chunk