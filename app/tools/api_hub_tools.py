import json
from app.services.integrations.api_hub import api_hub
from .registry import register_tool

@register_tool("slack_tool")
def slack_tool(tool_input: str, context: dict = None) -> str:
    """Send a Slack message. Expects JSON: {"channel": "#general", "message": "hello"}"""
    try:
        args = json.loads(tool_input)
        return api_hub.send_slack_message(args.get("channel", "#general"), args.get("message", ""))
    except Exception as e:
        return f"Error executing Slack tool: {e}"

@register_tool("jira_tool")
def jira_tool(tool_input: str, context: dict = None) -> str:
    """Create Jira ticket. Expects JSON: {"title": "Issue", "description": "Details", "priority": "High"}"""
    try:
        args = json.loads(tool_input)
        return api_hub.create_jira_ticket(args.get("title", ""), args.get("description", ""), args.get("priority", "Medium"))
    except Exception as e:
        return f"Error executing Jira tool: {e}"

@register_tool("salesforce_tool")
def salesforce_tool(tool_input: str, context: dict = None) -> str:
    """Fetch Salesforce account. Expects JSON: {"account_name": "Acme Corp"}"""
    try:
        args = json.loads(tool_input)
        return api_hub.fetch_salesforce_account(args.get("account_name", ""))
    except Exception as e:
        return f"Error executing Salesforce tool: {e}"
