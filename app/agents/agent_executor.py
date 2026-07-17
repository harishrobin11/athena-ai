from .planner import create_plan
from ..tools.registry import execute_tool
from ..providers.ollama_provider import ask_llm, stream_llm
from ..core.agent_prompt import AGENT_PROMPT
from .router import classify_query
import time


def run_agent(
    user_query: str,
    user_id=None,
    selected_documents=None,
    image_path=None,
):
    print("===== AGENT =====")
    print("QUERY:", user_query)
    route = classify_query(
        user_query,
        selected_documents,
    )
    print(f"Route: {route}")

    if image_path is not None:
        plan = [
            {
                "tool": "analyze_image",
                "input": user_query,
            }
        ]
    else:
        if route == "chat":
            print("Fast path -> Direct LLM")
            return ask_llm(
                [
                    {
                        "role": "user",
                        "content": user_query,
                    }
                ]
            )
        elif route == "memory":
            plan = [
                {
                    "tool": "search_memory",
                    "input": user_query,
                }
            ]
        elif route == "documents":
            plan = [
                {
                    "tool": "search_documents",
                    "input": user_query,
                }
            ]
        elif route == "calculator":
            plan = [
                {
                    "tool": "calculator",
                    "input": user_query,
                }
            ]
        else:
            print("Planner required")
            plan = create_plan(user_query)

    if not plan:
        return ask_llm(
            [
                {
                    "role": "user",
                    "content": user_query,
                }
            ]
        )

    # Execute tools
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
            print("Calling execute_tool...")
            start_tool = time.time()
            result = execute_tool(
                tool_name=tool_name,
                tool_input=tool_input,
                context=tool_context,
            )
            print(f"Tool took: {time.time() - start_tool:.2f} seconds")
            print("Tool returned:")
            print(result)
            tool_outputs.append(
                {
                    "tool": tool_name,
                    "success": True,
                    "result": result,
                }
            )
        except Exception as e:
            print(f"Tool Error: {e}")
            tool_outputs.append(
                {
                    "tool": tool_name,
                    "success": False,
                    "result": str(e),
                }
            )

    # =============================================
    # FAST PATH FOR IMAGE QUESTIONS
    # =============================================
    if image_path is not None:
        if tool_outputs:
            print("✅ Returning Vision Result Directly (non-stream)")
            return tool_outputs[0]["result"]

    tool_results = ""
    for output in tool_outputs:
        tool_results += f"""
    Tool:
    {output['tool']}
    Success:
    {output['success']}
    Result:
    {output['result']}
    """

    prompt = f"""
    {AGENT_PROMPT}
    User Question:
    {user_query}
    Available Information:
    {tool_results}
    Instructions:
    - Use all tool results.
    - Combine information from multiple tools.
    - Summarize retrieved conversations naturally.
    - If no relevant information exists, say so.
    """
    print("Sending prompt to LLM...")
    response = ask_llm(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    print("LLM finished.")
    return response


def run_agent_stream(
    user_query: str,
    user_id=None,
    selected_documents=None,
    image_path=None,
):
    print("===== AGENT (STREAM) =====")
    print("QUERY:", user_query)
    route = classify_query(
        user_query,
        selected_documents,
    )
    print(f"Route: {route}")

    if image_path is not None:
        print("Image detected")
        plan = [
            {
                "tool": "analyze_image",
                "input": user_query,
            }
        ]
    else:
        if route == "chat":
            print("Fast path -> Direct Streaming")
            return stream_llm(
                [
                    {
                        "role": "user",
                        "content": user_query,
                    }
                ]
            )
        elif route == "memory":
            plan = [
                {
                    "tool": "search_memory",
                    "input": user_query,
                }
            ]
        elif route == "documents":
            plan = [
                {
                    "tool": "search_documents",
                    "input": user_query,
                }
            ]
        elif route == "calculator":
            plan = [
                {
                    "tool": "calculator",
                    "input": user_query,
                }
            ]
        else:
            print("Planner required")
            plan = create_plan(user_query)

    if not plan:
        return stream_llm(
            [
                {
                    "role": "user",
                    "content": user_query,
                }
            ]
        )

    # Execute tools
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
            result = execute_tool(
                tool_name=tool_name,
                tool_input=tool_input,
                context=tool_context,
            )
            print(f"Tool took: {time.time() - start_tool:.2f} seconds")
            # === DEBUG PRINT 1 ===
            print("========== TOOL RESULT ==========")
            print("Type :", type(result))
            print("Value:", repr(result))
            print("=================================")
            tool_outputs.append(
                {
                    "tool": tool_name,
                    "success": True,
                    "result": result,
                }
            )
        except Exception as e:
            print(f"Tool Error: {e}")
            tool_outputs.append(
                {
                    "tool": tool_name,
                    "success": False,
                    "result": str(e),
                }
            )

    # =============================================
    # FAST PATH FOR IMAGE QUESTIONS
    # =============================================

    if image_path is not None:
        if tool_outputs:
            result = tool_outputs[0]["result"]

            print("\n" + "=" * 70)
            print("AGENT RESULT")
            print("Type :", type(result))
            print("Value:", repr(result))
            print("=" * 70)

            print("✅ Returning Vision Result Directly (streaming)")

            def generator():
                text = "" if result is None else str(result)

                print("\n" + "=" * 70)
                print("GENERATOR")
                print("Type :", type(text))
                print("Value:", repr(text))
                print("=" * 70)

                yield text

            return generator()

    # Build tool_results
    tool_results = ""
    for output in tool_outputs:
        tool_results += f"""
    Tool:
    {output['tool']}
    Success:
    {output['success']}
    Result:
    {output['result']}
    """

    # === DEBUG PRINT 2 ===
    print("========== TOOL RESULTS ==========")
    print(tool_results)
    print("==================================")

    prompt = f"""
    {AGENT_PROMPT}
    User Question:
    {user_query}
    Available Information:
    {tool_results}
    Instructions:
    - Use all tool results.
    - Combine information from multiple tools.
    - Summarize retrieved conversations naturally.
    - If no relevant information exists, say so.
    """

    print("Streaming from LLM...")
    print("========== FINAL PROMPT ==========")
    print(prompt)
    print("==================================")

    # Your requested timing for Text LLM
    start = time.time()
    response = stream_llm(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )
    print("Text LLM started after", time.time() - start)

    return response