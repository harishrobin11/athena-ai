from app.agents.planner import create_plan

plan = create_plan(
    "Summarize leave check documents for cancellation"
)

print(plan)