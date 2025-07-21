
from src.helpers.logger import log_output
def requirement_agent(llm,state):
    system_prompt =f"Analyze the following software requirement and break it into user stories:\n{state['input']}"
    response = llm.invoke(system_prompt).content
    return log_output("RequirementAgent", {"user_stories": response})
