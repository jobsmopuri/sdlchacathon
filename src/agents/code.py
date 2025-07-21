from src.helpers.logger import log_output
def code_review_agent(llm, state):
    prompt = f"Review this code and provide feedback or respond with APPROVED:\n{state["code"]}"
    response = llm.invoke(prompt).content
    return log_output("CodeReviewAgent", {"code_review": response})