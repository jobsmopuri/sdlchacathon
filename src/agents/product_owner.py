from src.helpers.logger import log_output

def product_owner_agent(llm,state):
    system_prompt =f"Review the following user stories and respond with APPROVED or suggestions:\n{state['user_stories']}"
    response = llm.invoke(system_prompt).content
    return log_output("ProductOwnerAgent",{"po_review":response})