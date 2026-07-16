from app.agents.planner import create_plan

plan = create_plan(
    "Summarize Sprint 9 and search documents for cancellation"
)

print("PLAN:")
print(plan)