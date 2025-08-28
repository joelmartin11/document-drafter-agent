# 📝 Document Drafter Agent

---

## 📌 Overview

The **Document Drafter Agent** is an AI-powered assistant that helps you draft, update, and save documents in a conversational workflow. Built with **LangGraph**, **LangChain**, and **Groq Llama3-70B**, it provides an interactive drafting experience where you can iteratively refine content.

---

## 🚀 Features

* 🤖 AI-driven drafting with Llama3-70B (Groq).
* 🔄 Iterative workflow via **LangGraph**.
* 🛠️ Custom tools for `update` and `save`.
* 🔐 Secure API key management via `.env`.
* 📂 Clean project structure with `requirements.txt`.

---

## 📂 Project Structure

```
document-drafter-agent/
│── drafter_agent.py      # Main agent code
│── requirements.txt      # Python dependencies
│── .env.example          # Template for environment variables
│── .gitignore            # Ignore secrets and unnecessary files
│── README.md             # Project documentation
│── LICENSE               # License (MIT)
```

---

## ⚙️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/document-drafter-agent.git
   cd document-drafter-agent
   ```

2. **Set up a virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Mac/Linux
   .venv\Scripts\activate      # On Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   * Copy `.env.example` → `.env`
   * Add your **Groq API key** inside `.env`

     ```
     GROQ_API_KEY=your_api_key_here
     ```

---

## ▶️ Usage

Run the drafter agent:

```bash
python drafter_agent.py
```

Example interaction:

```
Human: Draft me an intro email for a client.
AI: Here's a first draft...
Human: Update it to sound more formal.
AI: Updated version...
Human: Save this as intro_email.txt
```

---

## 🔑 Environment Variables

The project uses a `.env` file to store secrets:

```
GROQ_API_KEY=your_api_key_here
```

Never commit your `.env` to GitHub. The `.gitignore` already ensures this.

---

## 🔄 Workflow

1. You give drafting instructions.
2. Agent uses **Groq Llama3-70B** to generate/refine text.
3. Use `update` tool to make edits.
4. Use `save` tool to save drafts.
5. Loop continues until you end the session.

---

## 📜 License

This project is licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

## 🙌 Acknowledgements

* [LangGraph](https://github.com/langchain-ai/langgraph)
* [LangChain](https://www.langchain.com/)
* [Groq](https://groq.com/) for high-speed inference
