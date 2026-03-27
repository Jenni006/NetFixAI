from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.agent import run_diagnostics  # you will implement this

app = FastAPI(title="NetFix AI Backend")

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    message: str

@app.post("/chat")
def chat(query: Query):
    user_input = query.message
    # Call your Python logic here
    response = run_diagnostics(user_input)  # return a string
    return {"response": response}