from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

from scraper import fetch_site_content 
from analyze_llm import analyze_in_chunks 
from time_tool import get_current_time
import json

app = BedrockAgentCoreApp()

tools_outputs = []

@tool
def get_news_tool(keyword: str, site: str = None):
    """
    Searches for news articles based on a keyword.
    """
    global tools_outputs
    news_data = fetch_site_content(keyword, site)

    result = {"result": news_data}
    print("TOOL === get_news_tool result ===")
    print(f"Tool returned {len(news_data)} articles.")
    if news_data:
        print("First article title:", news_data[0].get('title'))

    tools_outputs.append({"tool_name": "get_news_tool", "return_value": result})
    return result


@tool
def analyze_news_tool(news_json: str):
    """
    Analyzes a list of news articles using a Bedrock LLM model.
    - Input: JSON string of news articles (list of dicts with 'title' and 'content')
    - Output: Analysis text from Titan or Claude
    """
    global tools_outputs
    try:
        news_list = json.loads(news_json)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON input. Please provide valid news data."}

    print("TOOL === analyze_news_tool invoked ===")
    print(f"Analyzing {len(news_list)} articles...")

    analysis_results = analyze_in_chunks(
        [n.get("title", "") + " - " + n.get("content", "") for n in news_list]
    )

    combined_result = "\n\n".join(analysis_results)
    result = {"analysis": combined_result}

    tools_outputs.append({"tool_name": "analyze_news_tool", "return_value": result})
    return result


@tool
def get_time_tool():
    global tools_outputs
    current_time = {"current_time": get_current_time()}
    tools_outputs.append({"tool_name": "get_time_tool", "return_value": current_time})
    print("TOOL === get_time_tool ===")
    return current_time


model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
model = BedrockModel(
    model_id=model_id,
    region_name="us-east-1"
)

agent = Agent(
    model=model,
    tools=[get_news_tool, analyze_news_tool, get_time_tool],
    system_prompt = f"""
You are a helpful assistant that only uses tools to fetch news or get the current time.

- If the user requests recent or latest news, first call 'get_time_tool' to get the current time.
- After obtaining the current date, automatically generate a search query that includes "after:YYYY-MM-DD" (set to 1–2 days before the current date).
- Always include the "after:YYYY-MM-DD" parameter when searching for recent or latest news.
- Never write or generate news analysis, opinions, or summaries on your own.
- Always call 'get_news_tool' to fetch news results.
- Pass the user's keyword directly to 'get_news_tool'.
- If the user specifies a website, pass it as the 'site' argument to 'get_news_tool'.
- If no website is provided, 'get_news_tool' will automatically search across a default list of multiple news sources.
- After the tool returns, simply present the fetched results clearly to the user without additional commentary.
- Do not re-run any tool unless the user explicitly requests it again.
- Never re-run 'get_news_tool' for the same query within the same conversation turn, even if no results are found.
- If the user wants to analyze the news content, use 'analyze_news_tool'.
"""
)


@app.entrypoint
async def agent_bedrock(payload):
    global tools_outputs
    tools_outputs = []

    user_input = payload.get("prompt")
    print(f"\n--- Received user input: {user_input} ---")
    response = agent(user_input)

    text = response.message['content'][0]['text']

    result = json.loads(json.dumps({
        "text": text,
        "tools_called": tools_outputs
    }, ensure_ascii=False))

    print("=== Final returned result ===")
    print(result)
    return result


if __name__ == "__main__":
    print("🚀 Starting Bedrock News AgentCore App...")
    app.run()
