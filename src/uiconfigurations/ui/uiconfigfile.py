from configparser import ConfigParser

class Config:
    def __init__(self,config_file="./src/uiconfigurations/ui/uiconfigfile.ini"):
        self.config = ConfigParser()
        self.config.read(config_file)
    
    #method is get the list of LLM options to select
    def get_llm_options(self):
        return self.config["DEFAULT"].get("LLM_OPTIONS").split(", ")
    
    #get the relavent groq models 
    def get_groq_model_options(self):
        return self.config["DEFAULT"].get("GROQ_MODEL_OPTIONS").split(", ")
    
    #get the relavent Openai models
    def get_openai_model_options(self):
        return self.config["DEFAULT"].get("OPENAI_MODEL_OPTIONS").split(", ")
    
    
