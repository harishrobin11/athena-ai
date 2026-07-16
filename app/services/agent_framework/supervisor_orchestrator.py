from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

SUPERVISOR_SYSTEM_PROMPT = """
You are the elite Athena AI Master Supervisor running inside an isolated multi-tenant corporate enterprise architecture.
Your core objective is to analyze the incoming user query along with conversation history, update the structural execution plan, and delegate tasks to specialized sub-agents.

Available sub-agents you can route tasks to:
1. 'rag_worker': Specialized in searching, fetching, parsing, and contextualizing corporate documents, PDFs, tables, internal enterprise knowledge fields, and PAST CONVERSATION HISTORY (Memory Vault).
2. 'code_worker': Specialized in running explicit algorithmic logic, data processing operations, numbers math, and structural visualization queries.

Operational Instructions:
- Deconstruct complex, multi-step requests into actionable tasks.
- If the user asks to search, fetch, summarize, read a document, OR asks about past conversations or memories, YOU MUST output 'rag_worker' as the next_step.
- If the required corporate data has been successfully fetched and processed by rag_worker, or if the request requires direct conversation, output 'FINISH'.
- Respond ONLY with a clean, unquoted JSON object matching this exact schema:
{{
  "execution_plan": ["Step 1 description", "Step 2 description"],
  "next_step": "rag_worker" | "code_worker" | "FINISH",
  "reasoning": "Brief technical justification for the routing choice."
}}
"""

class AthenaSupervisorOrchestrator:
    def __init__(self, azure_llm: ChatOpenAI):
        self.llm = azure_llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SUPERVISOR_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages")
        ])
        # Forces structural JSON responses from the Azure OpenAI portal
        self.chain = self.prompt | self.llm.with_structured_output(dict, method="json_mode")

    async def execute(self, state: dict) -> dict:
        """Processes the active state history to dictate the next routing step."""
        try:
            response = await self.chain.ainvoke({"messages": state["messages"]})
            if not isinstance(response, dict):
                response = {}
        except Exception as e:
            print(f"[ORCHESTRATOR WARNING] JSON Parsing Error: {e}")
            response = {"next_step": "FINISH"}
            
        return {
            "next_step": response.get("next_step", "FINISH"),
            "execution_plan": response.get("execution_plan", [])
        }
