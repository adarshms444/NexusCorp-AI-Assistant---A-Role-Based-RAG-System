import os
from typing import Dict, List
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# --- Initialize ---
load_dotenv()
app = FastAPI(title="NexusCorp Analytics RAG API")
security = HTTPBasic()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Load Knowledge Base ---
try:
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = FAISS.load_local(
        "knowledge_base", 
        embeddings=embedding_function,
        allow_dangerous_deserialization=True
    )
    print("✅ Knowledge Base loaded successfully.")
except Exception as e:
    print(f"❌ Error loading Knowledge Base: {e}")
    vectordb = None

# --- LLM and Prompt Template ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True
)

# --- Main prompt for the final answer ---
prompt_template = ChatPromptTemplate.from_template("""
You are a helpful and accurate AI assistant for NexusCorp Analytics.
You are equipped with role-based access to company knowledge.
Your task is to provide accurate, concise, and professional answers to employee questions.
Your answers MUST be based ONLY on the context provided below.
If the context does not contain the answer, or if you cannot sufficiently answer based on the given context,
politely state that you do not have enough information to answer based on the available data for the user's role.
Do not use outside knowledge.
Focus your answers directly on the question asked.
When asked about full-year performance (e.g., "2024 KPIs"), prioritize information from comprehensive annual reports if available in the context.
Be friendly, concise, and professional.

Context:
{context}

Question: {message}

Answer:
""")

# --- Prompt for generating multiple queries ---
multi_query_prompt = ChatPromptTemplate.from_template(
    "You are an AI language model assistant. Your task is to generate 3 different versions of the given user question to retrieve relevant documents from a vector database. "
    "By generating multiple perspectives on the user question, your goal is to help the user overcome some of the limitations of distance-based similarity search. "
    "Provide these alternative questions separated by newlines. Original question: {question}"
)

# --- Dummy Users Database ---
users_db: Dict[str, Dict[str, str]] = {
    "Jeswin": {"password": "243019", "role": "analytics_and_technology"},
    "Gautham": {"password": "243018", "role": "marketing"},
    "Ajeem": {"password": "243005", "role": "finance"},
    "Samuel": {"password": "123456", "role": "hr"},
    "Adil": {"password": "678910", "role": "c-levelexecutives"},
    "Rashad": {"password": "246810", "role": "employee"},
    "Adarsh": {"password": "243002", "role": "marketing"},
    "Mehta": {"password": "112233", "role": "c-levelexecutives"}
}

# --- Authentication ---
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": credentials.username, "role": user["role"]}

# --- Endpoints ---
@app.get("/login")
def login(user: dict = Depends(authenticate)):
    return {"message": f"Welcome {user['username']}!", "role": user["role"]}

@app.post("/chat")
async def chat(request: Request):
    if not vectordb:
        raise HTTPException(status_code=500, detail="Knowledge Base not available.")

    try:
        data = await request.json()
        user_info = data["user"]
        message = data["message"]
        user_role = user_info["role"].lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request format.")

    search_kwargs = {'k': 6}
    docs = []
    
    if "c-levelexecutives" in user_role:
        # --- Multi-Query Fusion Retrieval for C-Level ---
        
        # 1. Create a chain to generate sub-questions from the original question.
        generate_queries_chain = multi_query_prompt | llm | StrOutputParser()
        
        # 2. Get the list of queries, including the original one.
        # Use .ainvoke for async compatibility in a FastAPI endpoint
        generated_queries = await generate_queries_chain.ainvoke({"question": message})
        queries = [message] + generated_queries.strip().split('\n')
        
        # 3. Retrieve documents for each query and collect them all.
        all_retrieved_docs = []
        for q in queries:
            retrieved = vectordb.similarity_search(q.strip(), **search_kwargs)
            all_retrieved_docs.extend(retrieved)
            
        # 4. "Fuse" the results by creating a unique set of documents.
        unique_docs = {doc.page_content: doc for doc in all_retrieved_docs}
        docs = list(unique_docs.values())
        print(f"✅ C-Level Fusion Retrieval: Found {len(docs)} unique documents from {len(queries)} queries.")

    elif "employee" in user_role:
        search_kwargs['filter'] = {'role': 'general'}
        docs = vectordb.similarity_search(message, **search_kwargs)
        
    else: # Handles all other departmental roles
        departmental_filter = {
            "$or": [
                {"role": {"$eq": user_role}},
                {"role": {"$eq": "general"}}
            ]
        }
        search_kwargs['filter'] = departmental_filter
        docs = vectordb.similarity_search(message, **search_kwargs)
    
    if not docs:
        return {"response": f"I'm sorry, I couldn't find any relevant information for your role: '{user_info['role']}'."}

    context = "\n\n".join([doc.page_content for doc in docs])

    # Generate the final response using the fused context.
    chain = prompt_template | llm
    # Use .ainvoke for async compatibility in a FastAPI endpoint
    response = await chain.ainvoke({
        "role": user_info['role'],
        "context": context,
        "message": message
    })

    return {"response": response.content}

