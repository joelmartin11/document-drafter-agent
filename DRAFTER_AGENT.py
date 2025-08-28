from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage , HumanMessage, AIMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

"""
Diagram of the agent’s workflow:
START → AGENT → TOOLS → (loop back to AGENT) → END

This shows that:
- The AGENT node talks to the LLM (chat model).
- The TOOLS node executes functions (update/save).
- After tools run, we either loop back (for more edits) or END (if saved).
"""

load_dotenv()  # loads environment variables from .env file

api_key = os.getenv("GROQ_API_KEY")  # fetch Groq API key from environment
if api_key:
    print("API key: ", api_key[:8] + "************")  # print first few chars for debugging
else:
    raise Exception("API key not found.")  # crash if no key found

# -----------GLOBAL VARIABLE---------------
"""
This variable stores the latest version of the document.
We keep it global so that tools (update/save) can modify it directly.
In LangGraph, the proper way would be "Injected State",
but here we keep it simple with a global string.
"""
document_content = ""


# ---------------------------DEFINE AGENT STATE-------------
# AgentState defines what "data" flows through the graph.
# It must contain a list of messages (conversation history).
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # add_messages ensures new msgs are appended properly


# --------------TOOL---------------------------
@tool(description="This tool will update the draft with the LLM's output which is to satisfy the user's demand")
def update(content: str) -> str:
    # This tool updates our global draft with new content provided by the LLM
    global document_content
    print("[DEBUG] update() called with:", repr(content[:100]))  # print first 100 chars for debugging
    document_content = content  # overwrite document_content
    print("[DEBUG] document_content after update:", repr(document_content[:100]))
    return f"Document has been updated successfully! The current draft is: \n{document_content}"


@tool()
def save(filename: str) -> str:
    """
    This tool saves the draft into a text file.
    It should be the *last* tool called (program ends after saving).
    """
    global document_content
    # If no .txt extension, add it automatically
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    try:
        # Open file in write mode and dump the content
        with open(filename, "w") as f:  # default encoding works fine for Unicode
            f.write(document_content)
        return f"File '{filename}' saved successfully."
    except Exception as e:
        # Return the error if something goes wrong
        return f"Error saving file '{filename}': {str(e)}"


# All available tools must be listed here
tools = [update, save]

# ----------------CHOOSE MODEL--------------
# Create a Groq LLM client with the llama3 model and bind our tools to it
model = ChatGroq(
    model="llama3-70b-8192",  # the reasoning + tool-calling model
    groq_api_key=api_key
).bind_tools(tools)  # this tells the model it can use update/save


# -----------------NODES AND INITIATING OUR LLM-------------
# This function will run inside the "agent" node of the graph
def model_call(state: AgentState) -> AgentState:
    # System message → gives strict rules to the LLM
    system_prompt = SystemMessage(content=f"""
    You are a helpful document drafter AI assistant. 
    Your job is to update, edit, and improve the document based on the user's instructions. 

    RULES:
    - NEVER output <tool-use>, JSON, or function call text.
    - When updating text, ALWAYS call the `update` tool with the full new text as the "content" argument.
    - NEVER print the document content in your chat reply.
    - When saving, ONLY call the `save` tool with a filename.
    - After a tool call, your *natural language reply* must be short and conversational (e.g., "I've updated the draft." or "File saved successfully.").

    The current document is: {document_content}
    """)

    # If no messages yet → this is the very first user input
    if not state["messages"]:
        user_input = input("I'm ready to help you update your draft. What would you like to do? ")
    else:
        user_input = input("What would you like to do? ")  # prompt for next action
    print(f"\nUSER: {user_input}")
    user_message = HumanMessage(content=user_input)  # wrap input in a HumanMessage

    # Combine system + previous history + new user message
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]
    response = model.invoke(all_messages)  # call LLM
    print(f"\nAI: {response.content}")  # show what LLM responded in plain text

    # If LLM decided to use a tool → print which tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"USING TOOLS: {[tc['name'] for tc in response.tool_calls]}")

    # Return updated message history to the graph
    return {"messages": add_messages(state["messages"], [user_message, response])}


# -----------------CONDITIONAL EDGE----------
# This function decides if graph should continue looping or end
def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    if not messages:
        return "continue"

    # Walk messages in reverse (from newest to oldest)
    for message in reversed(messages):
        if isinstance(message, ToolMessage):  # check if it's a tool result
            content_lower = message.content.lower()
            if "saved successfully" in content_lower:  # save tool succeeded
                return "end"  # stop the graph

    return "continue"  # otherwise, keep looping


# ---------THE ROBUST PRINT FUNCTION--------------------------
def print_messages(messages: list[BaseMessage]) -> None:
    """
    This function prints the last 3 messages of the conversation.
    Helps us debug without flooding console with everything.
    """
    if not messages:  # if no messages exist
        print("No messages yet.")
        return

    for message in messages[-3:]:  # only last 3 messages
        if isinstance(message, ToolMessage):  # if message came from tool
            print(f"[TOOL] {message.content}")
        else:
            message.pretty_print()  # Human/AI messages get nice formatting


# -------------------GRAPH DEFINITION----------------------
graph = StateGraph(AgentState)  # create state graph with AgentState schema
graph.add_node("agent", model_call)  # add agent node (LLM call)
graph.add_node("tools", ToolNode(tools))  # add tools node (executes update/save)

graph.set_entry_point("agent")  # agent node is the start point
graph.add_edge("agent", "tools")  # after agent, always go to tools

# Conditional edge → after tools, either loop back or end
graph.add_conditional_edges(
    "tools",
    should_continue,  # function to check if done
    {
        "continue": "agent",  # go back to agent
        "end": END  # stop graph
    }
)

app = graph.compile()  # compile into runnable app


# ----------FINALLY----------------
def run_document_agent():
    """
    Runs the document drafting agent until the user saves.
    """
    state: AgentState = {"messages": []}  # initialize empty conversation
    print("\n--- Document Drafting Agent Started ---\n")

    # Run the app step by step (stream yields node executions)
    for event in app.stream(state):
        for node_name, output_state in event.items():
            print(f"\n[DEBUG] Node executed → {node_name}")
            print_messages(output_state["messages"])  # show last messages

    print("\n--- Agent finished execution (document saved) ---")


# Entry point for script
if __name__ == "__main__":
    run_document_agent()
