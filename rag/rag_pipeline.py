from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage._lc_store import create_kv_docstore
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import pinecone

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import sys
from pathlib import Path
import shutil
import chromadb
from .utils.rag_utils import ChromaStore, add_elements, img_prompt_func, split_image_text_types, is_image_data
from .utils.pdf_processor import extract_markdown, extract_image_table
from .utils.summary_utils import summarize_figure_table, summarize_text, markdown_split, summarize_paper_context, extract_paper_title


def build_retriever(zotero_key, paper_path = None, user_exist = True, update = False):

    pc = Pinecone()
    index_list = pc.list_indexes().names()


    if (f"zotomind-{zotero_key.lower()}" not in index_list):

        pc = Pinecone()
        pc.create_index(
        name=f"zotomind-{zotero_key.lower()}",
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ))
    if not os.path.exists(f"../rag/attachments/database/{zotero_key}"):
        client = chromadb.PersistentClient(path=f"../rag/attachments/database/{zotero_key}")

    # create retriever with vetorestore and docstore
    id_key = "doc_id"

    cs = ChromaStore(f"../rag/attachments/database/{zotero_key}", "docstore")
    vectorstore = PineconeVectorStore(index_name=f"zotomind-{zotero_key.lower()}", embedding=OpenAIEmbeddings())
    store = create_kv_docstore(cs)
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )

    # if this is a new user or old user needs update
    if not user_exist or update:
        for paper in [os.listdir(paper_path)[0]]:
            if paper.endswith(".txt"):
                continue
            file_path = Path(paper_path) / paper
            # extract markdown
            texts = extract_markdown(file_path)
            title = extract_paper_title(texts)

            texts = markdown_split(texts)
            text_summaries = summarize_text(texts)
            paper_context  = summarize_paper_context("\n".join(texts[:2]))

            # extract figrues and tables

            paper_name = paper.split(".")[0]
            images_path = f"../rag/attachments/images/{paper_name}"

            os.makedirs(images_path, exist_ok=True)
            _ = extract_image_table(file_path, images_path)
            tables, table_summaries, figures, figure_summaries = summarize_figure_table(images_path, paper_context)
            shutil.rmtree(images_path)


            retriever = add_elements(retriever=retriever, 
                                     elements=texts,
                                     summaries=text_summaries,
                                     id_key=id_key,
                                     title=title,
                                     )
            retriever = add_elements(retriever=retriever, 
                                        elements=figures,
                                        summaries=figure_summaries,
                                        id_key=id_key,
                                        title=title,
                                        )
            retriever = add_elements(retriever=retriever, 
                                        elements=tables,
                                        summaries=table_summaries,
                                        id_key=id_key,
                                        title=title,
                                        )
            print("Finish 1 paper")
    return retriever



def retrieve(retriever, query):
    model = ChatOpenAI(temperature=0, model="gpt-4-vision-preview", max_tokens=1024)

    # RAG pipeline
    chain = (
        {
            "context": retriever | RunnableLambda(split_image_text_types),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(img_prompt_func)
        | model
        | StrOutputParser()
    )

    response = chain.invoke(query)

    images = []
    docs = retriever.invoke(query)

    for doc in docs:
        if is_image_data(doc.page_content):
            images.append(doc)
    return response, images