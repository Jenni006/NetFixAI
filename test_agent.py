from src.agent import query_netfix

print("Testing NetFix AI...\n")
print("=" * 50)

question = "What happened to ROUTER-LAB-01 between 08:10 and 08:20? Give me the root cause."
print(f"Question: {question}\n")
response = query_netfix(question)
print(response)
print("=" * 50)