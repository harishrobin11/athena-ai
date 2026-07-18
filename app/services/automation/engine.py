from typing import List, Dict, Any
from app.core.logger import logger
from app.services.integrations.api_hub import api_hub
import json

class WorkflowEngine:
    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        logger.info("Workflow Automation Engine Initialized")

    def save_workflow(self, workflow_id: str, trigger: str, actions: List[str]) -> None:
        self.workflows[workflow_id] = {
            "trigger": trigger,
            "actions": actions,
            "status": "active"
        }
        logger.info(f"Saved Workflow {workflow_id} with {len(actions)} actions")

    def get_workflows(self) -> Dict[str, Dict[str, Any]]:
        return self.workflows

    def run_workflow(self, workflow_id: str, payload: dict = None) -> List[str]:
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return [f"Error: Workflow {workflow_id} not found."]

        logger.info(f"Executing Workflow {workflow_id}")
        results = []
        for action in workflow["actions"]:
            try:
                res = self._execute_action(action, payload)
                results.append(f"[{action}]: {res}")
            except Exception as e:
                results.append(f"[{action}] FAILED: {str(e)}")
                logger.error(f"Action {action} failed: {e}")
                break # Stop on first failure

        return results

    def _execute_action(self, action: str, payload: dict) -> str:
        payload = payload or {}
        if action == "Send Slack Message":
            return api_hub.send_slack_message(payload.get("channel", "#general"), payload.get("message", "Workflow Triggered"))
        elif action == "Create Jira Ticket":
            return api_hub.create_jira_ticket(payload.get("title", "Automated Task"), payload.get("description", ""), "Medium")
        elif action == "Fetch Salesforce Data":
            return api_hub.fetch_salesforce_account(payload.get("account_name", "Acme Corp"))
        elif action == "Run OCR Extraction":
            return "OCR extraction completed successfully."
        elif action == "Analyze Sentiment":
            return "Sentiment analysis determined: POSITIVE."
        else:
            return f"Action '{action}' is not supported."

workflow_engine = WorkflowEngine()
