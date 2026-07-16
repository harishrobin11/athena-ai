def calculator_tool(
    tool_input,
    context,
):
    """
    Calculator tool.

    Parameters
    ----------
    tool_input : str
        Mathematical expression.

    context : dict
        Runtime context passed by the agent.
        (Unused for calculator.)
    """

    expression = tool_input

    try:
        result = eval(expression)

        return str(result)

    except Exception as e:
        return f"Error: {e}"