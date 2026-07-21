from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

SUPERVISOR_SYSTEM_PROMPT = """
You are the elite Athena AI Master Supervisor running inside an isolated multi-tenant corporate enterprise architecture.
Your core objective is to analyze the incoming user query along with conversation history, update the structural execution plan, and delegate tasks to specialized sub-agents.

Available sub-agents you can route tasks to:
1. 'rag_worker': Specialized in searching, fetching, parsing, and contextualizing corporate documents, PDFs, tables, internal enterprise knowledge fields, and PAST CONVERSATION HISTORY (Memory Vault).
2. 'code_worker': Specialized in running explicit algorithmic logic, data processing operations, numbers math, and structural visualization queries.
3. 'research_worker': Specialized in multi-step internet searches, web scraping, scientific paper summarization, and verifying external facts (Sprint 19).
4. 'document_worker': Specialized in deep, visual PDF analysis, large-scale textual knowledge extraction, and complex table understanding workflows (Sprint 20).
5. 'sql_worker': Specialized in generating secure SQL dialects, running dynamic relational database queries, and charting data analytics (Sprint 21).
6. 'workflow_worker': Specialized in multi-step automation, calling external APIs, and scheduling background cron tasks (Sprint 23).

Operational Instructions:
- Deconstruct complex, multi-step requests into actionable tasks.
- If the user asks about past conversations, memories, or internal unstructured vector data, output 'rag_worker'.
- If the user asks to search the LIVE INTERNET for current facts or news, output 'research_worker'.
- If the user asks to parse, read, extract, or layout analyze a specific PDF document (like an invoice), output 'document_worker'.
- If the user asks to query a database, analyze raw relational data, or run SQL metrics, output 'sql_worker'.
- If the user asks for numbers math, visualization, or structural logic, output 'code_worker'.
- If the user asks to automate a multi-step sequence, trigger an external API, or schedule a recurring background task, output 'workflow_worker'.
- IMPORTANT MULTI-AGENT CHAINING: Review the conversation history. If the user provided a multi-step request (e.g. "fetch data from SQL then calculate math on it") and only the FIRST step has been completed (e.g. you see a [Worker Result] from sql_worker), you MUST route to the NEXT appropriate worker (e.g. code_worker) rather than FINISH. Keep evaluating the `execution_plan` until ALL steps are solved.
- ONLY output 'FINISH' if the complete multi-step request has been fully satisfied by the workers, or if it is a simple request that requires direct casual conversation.
- Respond ONLY with a clean, unquoted JSON object matching this exact schema:
{{
  "execution_plan": ["Step 1 description", "Step 2 description"],
  "next_step": "rag_worker" | "code_worker" | "research_worker" | "document_worker" | "sql_worker" | "workflow_worker" | "FINISH",
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
        user_msg = ""
        for msg in reversed(state.get("messages", [])):
            if getattr(msg, "type", "") == "human":
                user_msg = str(msg.content).lower()
                break
        
        selected_docs = state.get("context_metadata", {}).get("selected_documents", [])
        has_worker_result = any(
            "[Worker Result]" in str(getattr(m, "content", "")) for m in state.get("messages", [])
        )

        # Fast-Path 1: If worker results are present, finish immediately
        if has_worker_result:
            return {"next_step": "FINISH", "execution_plan": []}

        # Fast-Path 2: Direct heuristic routing for PDFs/docs/search/code/queries
        if selected_docs or any(kw in user_msg for kw in ["pdf", "document", "file", "uploaded", "invoice", "extract", "summary", "analyze", "read"]):
            return {
                "next_step": "rag_worker",
                "execution_plan": ["Retrieve and analyze document context from vector vault"]
            }
        elif any(kw in user_msg for kw in ["search", "web", "google", "internet", "news", "latest"]):
            return {
                "next_step": "research_worker",
                "execution_plan": ["Perform live internet search"]
            }
        elif any(kw in user_msg for kw in ["sql", "database", "query", "table", "sales"]):
            return {
                "next_step": "sql_worker",
                "execution_plan": ["Query relational database"]
            }

        # LLM Structural Router fallback for complex ambiguous queries
        next_step = "FINISH"
        execution_plan = []
        try:
            import asyncio
            # Limit LLM orchestrator call to 4s to prevent long hangs
            response = await asyncio.wait_for(
                self.chain.ainvoke({"messages": state["messages"]}),
                timeout=4.0
            )
            if isinstance(response, dict):
                next_step = response.get("next_step", "FINISH")
                execution_plan = response.get("execution_plan", [])
        except Exception as e:
            print(f"[ORCHESTRATOR WARNING] Structural Router bypass: {e}")

        return {
            "next_step": next_step,
            "execution_plan": execution_plan
        }

