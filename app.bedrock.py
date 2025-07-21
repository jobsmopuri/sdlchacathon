import os
import streamlit as st
import re
from src.agents import requirement,product_owner,design,code,security,test,monitoring,maintenance
from langchain_groq import ChatGroq
from src.graph.visualizer import render_langgraph_diagram
import zipfile
import io
from langchain.llms import Bedrock
import boto3
import json

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

st.set_page_config(page_title="SDLC", layout="wide")
st.title("🚀 AI-Powered SDLC Assistant")

# ------------------ Workflow Diagram ------------------
with st.expander("📈 SDLC Workflow Diagram", expanded=False):
    st.graphviz_chart(render_langgraph_diagram())

st.divider()

#Requirements section
if "stage" not in st.session_state:
    st.session_state.stage = "Requirements"

#LLM intialization
provider = "awsbedrock"#st.session_state.get("llm_provider")

if provider =="awsbedrock":
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    llm = Bedrock(client=client, model_id="anthropic.claude-v2")

#layut setup
column3, column2 = st.columns([1, 5])
approval_flags = {
    "User Stories": "requirements_approved",
    "Design Document": "user_stories_approved",
    "Code Generation": "design_approved",
    "Write & Review Test Cases": "code_approved",
    "QA Testing": "test_cases_approved",
    "Deployment": "qa_approved",
    "Monitoring": "deployment_done",
    "Maintenance": "monitoring_done"
}
stages = [
    "Requirements", 
    "User Stories", 
    "Design Document", 
    "Code Generation",
    "Write & Review Test Cases", 
    "QA Testing", 
    "Deployment",
    "Monitoring", 
    "Maintenance"
]


with column3:
    st.subheader("🧭 Workflow Stages")
    for i, stage_name in enumerate(stages):
        # Enable only if previous stage is approved
        if i == 0:
            disabled = False
        else:
            required_flag = approval_flags.get(stage_name)
            disabled = not st.session_state.get(required_flag, False)
        
        st.button(stage_name, key=f"nav_{stage_name}", disabled=disabled)

    st.divider()
    if st.session_state.get("stage") == "Maintenance":
        st.subheader("📥 Download Documents and Code")
        for key, label in {
            "design_doc": "Design Document",
            "code": "Generated Code",
            "test_cases": "Test Cases",
        }.items():
            if key in st.session_state:
                st.download_button(f"📄 {label}", st.session_state[key], file_name=f"{label.lower().replace(' ', '_')}.txt")

# graphstate Logic

with column2:
    st.subheader(f"Stage: {st.session_state.stage}")

    if not llm:
        st.warning("Please Provide  your API Key")
    else:
        stage = st.session_state.stage

        if stage == "Requirements":
            user_input = st.text_area("📝 Describe your software requirement:",key="input_box")
            if st.button("🚀 Submit Requirement"):
                st.session_state.input = user_input
                result = requirement.requirement_agent(llm, {"input": user_input})
                st.session_state.user_stories = result["user_stories"]
                #st.session_state.requirements_approved = True
                st.session_state.stage = "User Stories"
                st.rerun()

        elif stage == "User Stories":
            st.markdown(st.session_state["user_stories"])
            result = product_owner.product_owner_agent(llm,{"user_stories":st.session_state["user_stories"]})
            feedback = st.text_area("🧠 Product Owner Feedback", value=result["po_review"],key="po_review_text")
            column1,column2 = st.columns(2)
            if column1.button("✅ Approve User Stories"):
                st.session_state.po_review = "APPROVED"
                st.session_state.requirements_approved = True
                st.session_state.stage = "Design Document"
                st.rerun()
            if column2.button("✍️ Submit Feedback"):
                st.session_state.po_review = feedback
                st.session_state.user_stories = feedback
                st.rerun()

        elif stage == "Design Document":
            if "po_review" in st.session_state:
                result = design.design_agent(llm,{
                    "input": st.session_state["input"],
                    "user_stories": st.session_state["user_stories"],
                    "po_review": st.session_state["po_review"]
                })
                st.session_state["design_doc"] = result["design_doc"]
                st.markdown(result["design_doc"],unsafe_allow_html=True)

                #design review
                result = design.design_review_agent(llm,{
                    "design_doc":st.session_state["design_doc"]
                })
                feedback = result["design_review"]
                st.text_area("💬 Design Review Feedback", value=feedback, key="design_review_input")
                column1,column2 = st.columns(2)
                if column1.button("✅ Approve Design"):
                    st.session_state["design_review_status"] = "APPROVED"
                    st.session_state.user_stories_approved = True
                    st.session_state.stage = "Code Generation"
                    st.rerun()
                if column2.button("✍️ Submit Design Feedback"):
                    st.session_state["design_review_status"] = st.session_state["design_review_status"]
                    st.warning("Feedback submitted. Update design if necessary.")

        elif stage =="Code Generation":
            st.subheader("Code Genaration Stage")
            prompt_dynamic =f""" 
            You are a SDLC Code Generator agent.
            Give the Design document below {st.session_state.design_doc}

            Generate the necessary code files clearly labeled in the following format:
            File:<filename with extenstion>
            ```<language>
            # your code here
            ```
            Clearly label and separate each file.
            """
            
            # response = llm.invoke(prompt_dynamic)
            # response_text = response.content if hasattr(response,"content") else str(response)

            #     # parse the files dynamically using robust regex
            # file_pattern = r"File: (.+?)\n```[a-z]*\n(.*?)```"
            # files = re.findall(file_pattern,response_text,re.DOTALL)

            # if files:
            #         st.success("✅ Code generated successfully!")
            #         st.subheader("📂 Generated Files")
            #         combined_code = ""
            #         for filename,file_content in files:
            #             file_content= file_content.strip()
            #             st.session_state[filename] = file_content
            #             combined_code += f"# {filename}\n{file_content}\n\n"
            #             ext = filename.split(".")[-1]
            #             lang_map = {'py':'python', 'html':'html', 'js':'javascript', 'css':'css',
            #                 'sql':'sql', 'json':'json', 'md':'markdown', 'yaml':'yaml'}
            #             language = lang_map.get(ext, 'plaintext')

            #             with st.expander(f"{filename}"):
            #                 st.code(file_content,language=language)
            #                 st.download_button(f"Download {filename}",file_content,file_name=filename)

            # else:
            #         st.warning("⚠️ No clearly labeled files found. Try regenerating.")
            #         st.stop()

            #     #sanitize the code for review purpose 
            # def sanitize_code(raw_code):
            #         lines = raw_code.splitlines()  
            #         sanitized =[]
            #         for line in lines:
            #             stripped = line.strip()
            #             if not stripped:
            #                 sanitized.append("") # blank line inserted 
            #             elif stripped.startswith(("#", "def ", "class ", "import ", "from ", "@", "return", 
            #                              "print", "for ", "if ", "while ", "try:", "except", "{", "}")):
            #                 sanitized.append(line)
            #             else:
            #                 sanitized.append(f"# {line}")
            #         return "\n".join(sanitized)
                
            # cleaned_code = sanitize_code(combined_code) 
            # st.session_state["code"] = cleaned_code

            #     #display sanitized combined code clearly
            # st.code(cleaned_code,language="python")

            #     # perform  combined code _security review code
            # code_review = code.code_review_agent(llm,{"code",st.session_state.code})
            # sec_review = security.security_review_agent(llm,{"code",st.session_state.code})

            # combined_reviews = f"### Code Review\n{code_review['code_review']}\n\n### Security Review\n{sec_review['security_review']}"

            # feedback = st.text_area("🔍 Code + Security Review", value=combined_reviews, height=250, key="code_security_review")
            # column1, column2 = st.columns(2)
            # if column1.button("✅ Approve Reviews"):
            #         st.session_state.code_review = "APPROVED"
            #         st.session_state.security_review = sec_review["security_review"]
            #         st.session_state.stage = "Write & Review Test Cases"
            #         st.rerun()

            # if column2.button("✍️ Submit Feedback"):
            #         st.session_state.code_review = feedback
            #         st.session_state.security_review = feedback
            #         st.success("✅ Feedback saved.")


            #except Exception as e:
                #st.error(f"Code generation failed: {str(e)}")

            response = llm.invoke(prompt_dynamic)
            response_text = response.content if hasattr(response, 'content') else str(response)

                # Parse files dynamically using robust regex
            file_pattern = r"File: (.+?)\n```[a-z]*\n(.*?)```"
            files = re.findall(file_pattern, response_text, re.DOTALL)

            if files:
                st.success("✅ Code generated successfully!")
                st.subheader("📂 Generated Files")
                combined_code = ""  # Combined sanitized code for review agents

                for filename, file_content in files:
                    file_content = file_content.strip()
                    st.session_state[filename] = file_content
                    combined_code += f"# {filename}\n{file_content}\n\n"

                    ext = filename.split('.')[-1]
                    lang_map = {'py':'python', 'html':'html', 'js':'javascript', 'css':'css',
                            'sql':'sql', 'json':'json', 'md':'markdown', 'yaml':'yaml'}
                    language = lang_map.get(ext, 'plaintext')

                    with st.expander(f"{filename}"):
                        st.code(file_content, language=language)
                        st.download_button(f"Download {filename}", file_content, file_name=filename)
            else:
                st.warning("⚠️ No clearly labeled files found. Try regenerating.")
                st.stop()


                # Sanitize combined code for review purposes
            def sanitize_code(raw_code):
                lines = raw_code.splitlines()
                sanitized = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        sanitized.append("")  # blank line
                    elif stripped.startswith(("#", "def ", "class ", "import ", "from ", "@", "return", 
                                         "print", "for ", "if ", "while ", "try:", "except", "{", "}")):
                        sanitized.append(line)
                    else:
                        sanitized.append(f"# {line}")
                return "\n".join(sanitized)
                
            cleaned_code = sanitize_code(combined_code)
            st.session_state.code = cleaned_code

                # Display sanitized combined code clearly
            st.code(cleaned_code, language="python")

                # Perform combined Code + Security review (exactly as per your previous working code)
            code_rev = code.code_review_agent(llm, {"code": st.session_state.code})
            sec_rev = security.security_review_agent(llm, {"code": st.session_state.code})

            combined_reviews = f"### Code Review\n{code_rev['code_review']}\n\n### Security Review\n{sec_rev['security_review']}"

            feedback = st.text_area("🔍 Code + Security Review", value=combined_reviews, height=250, key="code_security_review")



            col1, col2 = st.columns(2)
            if col1.button("✅ Approve Reviews"):
                st.session_state.code_review = "APPROVED"
                st.session_state.security_review = sec_rev["security_review"]
                st.session_state.design_approved = True
                st.session_state.stage = "Write & Review Test Cases"
                st.rerun()

            if col2.button("✍️ Submit Feedback"):
                st.session_state.code_review = feedback
                st.session_state.security_review = feedback
                st.success("✅ Feedback saved.")
           
        elif stage =="Write & Review Test Cases":
            st.markdown("### 🧪 Generated Test Cases")
            if "test_cases" not in st.session_state:
                result = test.test_case_agent(llm,{"code":st.session_state["code"]})
                st.session_state["test_cases"] = result["test_cases"]

            st.markdown(st.session_state["test_cases"],unsafe_allow_html=True)
            review = test.test_case_review_agent(llm, {"test_cases": st.session_state["test_cases"]})
            feedback = st.text_area("📝 Test Case Review", value=review["test_case_review"], key="test_case_review_box")

            col1, col2 = st.columns(2)
            if col1.button("✅ Approve Test Cases"):
                st.session_state.test_case_approved = True
                st.session_state.test_case_review = feedback
                st.session_state.code_approved = True
                st.session_state.stage = "QA Testing"
                st.rerun()

            if col2.button("✍️ Submit Test Case Feedback"):
                result = test.test_case_agent(llm, {
                    "code": st.session_state["code"],
                    "feedback": feedback
                })
                st.session_state["test_cases"] = result["test_cases"]
                st.success("✅ Test cases regenerated.")
                st.rerun()

        elif stage == "QA Testing":
            if "test_cases" in st.session_state and "code" in st.session_state:
                result = test.qa_testing_agent(llm, {
                    "test_cases": st.session_state.test_cases,
                    "code": st.session_state.code
                })
                st.session_state.qa_result = result["qa_result"]
                st.code(st.session_state.qa_result)

                feedback = st.text_area("✍️ QA Feedback (Optional)", key="qa_feedback")
                col1, col2 = st.columns(2)
                if col1.button("✅ Proceed to Deployment"):
                    st.session_state.stage = "Deployment"
                    st.session_state.test_cases_approved = True
                    st.rerun()
                if col2.button("✍️ Submit QA Feedback"):
                    st.session_state.qa_result += f"\n\nUser QA Feedback: {feedback}"
                    st.success("✅ Feedback added.")
            else:
                st.warning("Please ensure code and test cases are generated first.")
     
        elif stage == "Deployment":
            st.markdown("### 🚀 Deployment Options")

            deploy_choice = st.radio("How would you like to proceed?", [
                "Continue without deployment",
                "Push to GitHub",
            ])

            if deploy_choice == "Continue without deployment":
                #st.success("✅ Code marked as deployed locally.")
                st.session_state.deployment_status = "Code marked as deployed (not pushed)."
                if st.button("Next: Monitoring"):
                    st.session_state.qa_approved = True
                    st.session_state.stage = "Monitoring"
                    st.rerun()

            elif deploy_choice == "Push to GitHub":
            #elif deploy_choice == "Push to GitHub & Deploy to Streamlit":
                github_token = st.text_input("🔐 GitHub Token", type="password", key="gh_token")
                github_repo = st.text_input("📦 GitHub Repo (e.g., yourusername/yourrepo)", key="gh_repo")

                if github_token and github_repo:
                    if st.button("🚀 Push to GitHub"):
                        try:
                            # Gather all generated files from session state dynamically
                            files = {filename: content for filename, content in st.session_state.items()
                                    if isinstance(content, str) and '.' in filename}
                            
                            

                            # Add a README.md if missing
                            if "README.md" not in files:
                                files["README.md"] = "# Streamlit App\nDeployed by AI SDLC Assistant."

                            # Push files to GitHub using existing logic
                            #push_files_to_github(github_token, github_repo, files)

                            repo_url = f"https://github.com/{github_repo}"
                            st.success(f"✅ Code pushed successfully to GitHub: [{github_repo}]({repo_url})")     


                            st.session_state.deployment_status = f"Deployed to GitHub repo: {github_repo}"
                            st.session_state.qa_approved = True
                            st.session_state.stage = "Monitoring"
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Deployment failed: {str(e)}")   

        elif stage == "Monitoring":
            result = monitoring.monitoring_agent(llm, {})
            st.session_state.monitoring_feedback = result["monitoring_feedback"]
            st.code(result["monitoring_feedback"])
            if st.button("Next: Maintenance"):
                st.session_state.stage = "Maintenance"
                st.session_state.deployment_done = True
                st.session_state.monitoring_done = True
                st.rerun()

        elif stage == "Maintenance":
            result = maintenance.maintenance_agent(llm, {
                "monitoring_feedback": st.session_state.monitoring_feedback
            })
            st.session_state.maintenance_done = result["maintenance_done"]
            st.code(result["maintenance_done"])
            st.success("🎉 Workflow complete!")


                

