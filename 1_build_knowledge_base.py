# 1_build_knowledge_base.py

import os
import shutil
from langchain_unstructured import UnstructuredLoader # For general markdown loading
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

# --- Configuration ---
DATA_DIR = "assets/data"
KB_DIR = "knowledge_base"

embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# --- Aggregate all split documents ---
all_split_docs = []

for department in os.listdir(DATA_DIR):
    dept_path = os.path.join(DATA_DIR, department)

    if os.path.isdir(dept_path):
        print(f"\n🔍 Processing department: {department}")
        
        # We will process each file individually to apply the best splitter
        for file in os.listdir(dept_path):
            file_path = os.path.join(dept_path, file)
            split_docs_for_file = []

            try:
                if file.endswith(".md"):
                    # Use MarkdownHeaderTextSplitter for Markdown files
                    # Define headers to split by. The content below these headers will form chunks.
                    headers_to_split_on = [
                        ("#", "Header1"),  # Top-level report title
                        ("##", "Header2"), # Sections like Executive Summary, Campaign Analysis
                        ("###", "Header3"), # Sub-sections
                    ]
                    
                    # Load the raw text content
                    with open(file_path, "r", encoding="utf-8") as f:
                        markdown_text = f.read()
                    
                    markdown_splitter = MarkdownHeaderTextSplitter(
                        headers_to_split_on=headers_to_split_on
                    )
                    md_chunks = markdown_splitter.split_text(markdown_text)
                    
                    # Further split large Markdown chunks using RecursiveCharacterTextSplitter
                    # This handles cases where a single header section is very long
                    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=70)
                    for chunk in md_chunks:
                        # Ensure chunk.page_content is not empty before splitting
                        if chunk.page_content.strip():
                            # The MarkdownHeaderTextSplitter already adds metadata based on headers
                            # We retain existing metadata and add department role
                            sub_chunks = recursive_splitter.split_documents([chunk])
                            for sub_chunk in sub_chunks:
                                sub_chunk.metadata.update(chunk.metadata) # Merge metadata
                                split_docs_for_file.append(sub_chunk)
                        
                elif file.endswith(".csv"):
                    loader = CSVLoader(file_path)
                    docs = loader.load()
                    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=70)
                    split_docs_for_file.extend(recursive_splitter.split_documents(docs))
                else:
                    continue # Skip other file types

                # Add metadata (role and category for 'general' dept) to all chunks from this file
                for doc in split_docs_for_file:
                    doc.metadata["role"] = department.lower()
                    if department.lower() == "general":
                        doc.metadata["category"] = "general"

                all_split_docs.extend(split_docs_for_file)
                print(f"✅ Loaded & split {len(split_docs_for_file)} chunks from '{file}' for '{department}'")

            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")

        if not split_docs_for_file: # Check if any docs were processed for the department
            print(f"⚠️ No documents found for department: {department}")
            continue


# --- Build or refresh FAISS Knowledge Base ---
if os.path.exists(KB_DIR):
    shutil.rmtree(KB_DIR)
    print(f"🧹 Removed old knowledge base.")

db = FAISS.from_documents(documents=all_split_docs, embedding=embedding_model)
db.save_local(KB_DIR)

# --- Summary ---
print(f"\n🎉 Successfully built the knowledge base with {len(all_split_docs)} documents.")
print(f"   Saved to directory: '{KB_DIR}'")