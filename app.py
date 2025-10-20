import boto3
import json
import uuid
import streamlit as st
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION", "ap-southeast-2")
aws_region = os.getenv("AWS_REGION", "ap-southeast-2")

AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")
try:
    agent_core_client = boto3.client(
        "bedrock-agentcore",
        region_name=aws_region
    )
except Exception as e:
    st.error(f"Failed to create Boto3 client. Please check your AWS credentials. Error: {e}")
    st.stop()

st.set_page_config(page_title="AI News Chatbot", layout="wide")
st.title("🤖 AI News Analysis Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "news_links" not in st.session_state:
    st.session_state.news_links = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

with st.sidebar:
    st.header("Options")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.news_links = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.header("News Sources")
    if st.session_state.news_links:
        for source in st.session_state.news_links:
            # Use Markdown format to create clickable hyperlinks
            st.markdown(f"- [{source['title']}]({source['link']})")
    else:
        st.info("News sources will appear here after a search.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about a company or topic..."):
    if not prompt.strip():
        st.warning("Please enter a valid message!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching for news and generating a summary..."):
                full_response = ""
                retrieved_news_links = []
                try:
                    agent_response = agent_core_client.invoke_agent_runtime(
                        agentRuntimeArn=AGENT_RUNTIME_ARN,
                        runtimeSessionId=st.session_state.session_id,
                        payload=json.dumps({"prompt": prompt}).encode(),
                        contentType="application/json"
                    )

                    body = agent_response.get("response")
                    if body:
                        response_body_str = body.read().decode('utf-8')
                        logging.info(f"RAW RESPONSE BODY: {response_body_str}")

                        data = json.loads(response_body_str)
                        
                        full_response = data.get("text", "No text response found.")
                        
                        tools = data.get("tools_called", [])
                        for tool in tools:
                            return_value = tool.get("return_value", {})
                            result = return_value.get("result", [])
                            for item in result:
                                if item.get("link") and item.get("title"):
                                    retrieved_news_links.append({"title": item["title"], "link": item["link"]})
                    else:
                        full_response = "Received an empty response from the Agent. Please check the backend logs."

                except Exception as e:
                    full_response = f"⚠️ An error occurred while invoking the Agent: {str(e)}"
                    st.error(full_response)
                    logging.error(full_response, exc_info=True)

            st.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            if retrieved_news_links:
                st.session_state.news_links = retrieved_news_links
                st.rerun()
