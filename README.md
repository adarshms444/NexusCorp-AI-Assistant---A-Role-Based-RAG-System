# NexusCorp Assistant

### A Role-Based Retrieval-Augmented Generation (RAG) System for Secure Enterprise Knowledge Access

---

## 📌 Project Overview
**NexusCorp Assistant** is a secure, role-aware AI chatbot built using **Retrieval-Augmented Generation (RAG)**. It enables employees to query internal company documents using natural language while ensuring **strict role-based access control (RBAC)**.

The system combines:
* **Semantic Search:** Using vector embeddings to understand context.
* **Secure Retrieval:** Filtering documents based on user roles before they reach the LLM.
* **Grounded Generation:** Using Google Gemini to answer questions strictly based on retrieved company data.

---

## 🏢 About NexusCorp Analytics
**NexusCorp Analytics** is a data analytics and AI consulting firm handling sensitive internal reports, performance documents, and operational data across multiple departments:
* 📈 **Marketing**
* 💰 **Finance**
* 👥 **Human Resources**
* 📊 **Analytics**
* 📜 **General Company Policies**

As the company scaled, managing and securely accessing this siloed knowledge became a critical bottleneck.

---

## ❓ Problem Statement
Employees at NexusCorp faced significant challenges:
1.  **Information Silos:** Knowledge was scattered across disconnected folders.
2.  **Inefficient Search:** Keyword-based search failed to find relevant answers.
3.  **Security Risks:** Sensitive financial or HR data risked exposure to unauthorized staff.
4.  **LLM Hallucinations:** Generic chatbots invented answers or leaked confidential info.

**The Goal:** A solution that understands *meaning*, retrieves accurate info, and enforces *who sees what*.

---

## 💡 Solution Architecture
The NexusCorp Assistant solves these problems using a **RAG + RBAC** architecture.

### Core Workflow:
1.  **Ingestion:** Convert company documents into vector embeddings.
2.  **Metadata Tagging:** Attach specific role permissions (e.g., `role: finance`) to each document chunk.
3.  **Storage:** Index vectors in a **FAISS** database.
4.  **Retrieval:** When a user queries, the system filters results based on their login role *before* context generation.
5.  **Generation:** The LLM generates an answer using only the authorized context.

---

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Framework:** LangChain
* **LLM:** Google Gemini (via Google Generative AI)
* **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
* **Vector Database:** FAISS (Facebook AI Similarity Search)
* **Backend API:** FastAPI
* **Frontend UI:** Streamlit

---

## 📂 Project Structure

```bash
NexusCorp-Assistant/
├── assets/
│   └── data/                 # Source documents organized by department
│       ├── marketing/
│       ├── finance/
│       ├── hr/
│       └── general/
├── knowledge_base/           # Generated FAISS index stores
├── 1_build_knowledge_base.py # Script to ingest data and build vectors
├── api_server.py             # FastAPI backend handling logic & auth
├── 3_chatbot_ui.py           # Streamlit frontend for user interaction
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API Keys)
└── README.md                 # Project documentation

```

## 💻 Setup & Run

1. Clone the repository:

```bash
git clone https://github.com/your-username/NexusCorp-Assistant.git
cd NexusCorp-Assistant
```

2. Create a virtual environment and activate it (Windows):

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure Environment Variables:
Create a .env file at the project root and add your Google API Key:

```
GOOGLE_API_KEY="your_google_gemini_api_key_here"

```
5. Build the Knowledge Base:
Run the ingestion script to process documents and create the FAISS index.

```
python 1_build_knowledge_base.py
```

6. Start the API Server:
Launch the FastAPI backend.

```
uvicorn api_server:app --reload
```

7. Run the Chat Interface:
Open a new terminal (keep the API running) and launch the Streamlit app.

```
streamlit run 3_chatbot_ui.py
```


---

## 🚫 What This System Prevents
* Cross-department data exposure
* Hallucinated enterprise answers
* Keyword-only search failures

---
