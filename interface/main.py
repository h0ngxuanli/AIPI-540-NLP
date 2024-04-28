import warnings
warnings.filterwarnings("ignore")

import subprocess
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pyzotero
from datetime import datetime
from rag.rag_pipeline import build_retriever, retrieve
from rag.utils.zoto_utils import initialize_zotero
from rag.utils.zoto_utils import pull_paper_parallelized, initialize_zotero, get_paper_keys, get_meta_data
from rag.utils.inference_utils import convert_to_latex
import subprocess
import streamlit as st
from pathlib import Path




def main():

    # Initialize title
    user_exits = False
    update = False
    gradient_text_html = """
    <style>
    .gradient-text {
        font-weight: bold;
        background: -webkit-linear-gradient(left, red, grey);
        background: linear-gradient(to right, red, grey);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline;
        font-size: 3em;
    }
    </style>
    <div class="gradient-text">ZotoMind</div>
    """
    st.markdown(gradient_text_html, unsafe_allow_html=True)
    st.caption("Dive into Zotero, Emerge with Answers and Insights.")
    model = "GPT-4"
    st.session_state["model"] = model


    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to ZotoMind, your smart companion in the world of Zotero! 📚✨"}
        ]

    if "response" not in st.session_state:
        st.session_state["response"] = None

    for id, message_text in enumerate(st.session_state.messages):
        st.chat_message(name = "user" if message_text["role"] == "user" else "assistant").markdown(message_text["content"])
            
            


    # Initialize sidebar
    with open("interface/sidebar/styles.md", "r") as styles_file:
        styles_content = styles_file.read()
    st.write(styles_content, unsafe_allow_html=True)


    # Set API keys
    # Zotero API Key
    st.sidebar.header('Zotero API Key🔑')
    zotero_api_key = st.sidebar.text_input('', key='Zotero Key', type="password")
    if zotero_api_key:
        st.sidebar.success('Zotero API Key entered!')

    # Zotero library ID
    st.sidebar.header('Zotero Library ID🗝️')
    library_id = st.sidebar.text_input('', key='Zotero Libr', type="password")
    if library_id:
        st.sidebar.success('Zotero Library ID entered!')


    with st.sidebar:
        "[Get Your Zotero API Key & Library ID](https://www.zotero.org/settings/keys)"

    # GPT4 key
    st.sidebar.header('GPT-4 API Key🔑')
    openai_api_key = st.sidebar.text_input('', key='GPT-4 Key', type="password")
    if openai_api_key:
        st.sidebar.success('OpenAI API Key entered!')
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Huggingface key
    st.sidebar.header('HuggingFace API Key🤗')
    hf_api_key = st.sidebar.text_input('', key='HF Key', type="password")
    if  hf_api_key:
        st.sidebar.success('HuggingFace API Key entered!')
        os.environ["HF_API_KEY"] = hf_api_key

    # Pinecone key
    st.sidebar.header('PineCone API Key🌰')
    pinecone_api_key = st.sidebar.text_input('', key='PineCone Key', type="password")
    if  pinecone_api_key:
        st.sidebar.success('PineCone API Key!')
        os.environ["PINECONE_API_KEY"] = pinecone_api_key

    # check whether database is the latest one
    paper_dir = f"../rag/attachments/papers/{zotero_api_key}/"
    database_dir = f"../rag/attachments/database/{zotero_api_key}/"

    if st.sidebar.button("Check Database"):

        if library_id:
            try:
                library_id = int(library_id)
            except:
                st.info("Your Libray ID should be Integer!")
                st.stop()
        # check whether exist data and show status
        if os.path.exists():
            with open(Path(paper_dir)/"latest_time.txt", 'r') as file:
                # Read the contents of the file
                latest_time =  file.read()
            latest_time = datetime.strptime(latest_time, '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d")
            st.session_state['db_status'] = f'<p style="color: green;"><strong>Database last updated on: {latest_time}</strong></p>'
        else:
            st.session_state['db_status'] = '<p style="color: red;"><strong>You have not built your database</strong></p>'
        st.sidebar.markdown(st.session_state['db_status'], unsafe_allow_html=True)


    # pull the latest papers and register them into vector database
    if st.sidebar.button("Updating Database") & (zotero_api_key is not None) & (library_id is not None):
        st.session_state.messages.append({"role": "assistant", "content": "Start building database for your Zotero collections 💡 ... "})
        st.chat_message(name = "assistant").markdown("Start building database for your Zotero collections 💡 ... ")
        zot = initialize_zotero(library_id = library_id, api_key = zotero_api_key)
        if os.path.exists(database_dir):
            user_exits = True
            with open(Path(paper_dir)/"latest_time.txt", 'r') as file:
                latest_time =  file.read()
            try:
                update = True
                latest_time = pull_paper_parallelized(zot, 
                                        file_path = paper_dir, 
                                        num_processes = 5, 
                                        latest_time = latest_time)
            except pyzotero.zotero_errors.UserNotAuthorised:
                st.error("Your Zotero Key is Wrong!")
                st.stop()

            except Exception as e:
                latest_time = latest_time 
        
        else:
            user_exits = False
            update = False
            if not os.path.exists(paper_dir):
                os.mkdir(paper_dir)
            
            latest_time = pull_paper_parallelized(zot, 
                                    file_path = paper_dir, 
                                    num_processes = 5, 
                                    latest_time = None)
            
        # update latest time
        with open(f"../rag/attachments/papers/{zotero_api_key}/latest_time.txt", 'w') as file:
            file.write(latest_time)
        
        # print the paper that needed to be updated
        sorted_keys, sorted_added_time = get_paper_keys(zot)
        papers = []
        for i in range(5):
            meta_data_info = get_meta_data(zot, sorted_keys[i])
            papers.append(meta_data_info)

        markdown_string = "# Papers in your database\n"
        for paper in papers:
            markdown_string += f"## {paper['title']}\n"
            markdown_string += "- **Added Date**: {}\n".format(datetime.strptime(paper['dateAdded'], '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d"))
            markdown_string += f"- **Authors**: {', '.join(paper['creators'])}\n"
            markdown_string += f"- **Field**: {paper['tags']}\n\n"



    # start building retriever
        st.session_state.messages.append({"role": "assistant", "content": markdown_string})
        # message(markdown_string, is_user = False)
        st.chat_message(name = "assistant").markdown(markdown_string)

        response = "Your database is all set 🥳!"
        st.session_state.messages.append({"role": "assistant", "content": response})
        # message(response, is_user = False)
        st.chat_message(name = "assistant").markdown(response)

        response = "Start building a unique ZotoMind for uuuu 🧠!"
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message(name = "assistant").markdown(response)

        
        if zotero_api_key == "3WYiWAu8bLIX6pIo6IBhYkJs":
            retriever = build_retriever(
                            zotero_key = "10papers", 
                            paper_path = None,
                            user_exist = True, 
                            update = False
                            )
        else:
            retriever = build_retriever(
                zotero_key = zotero_api_key, 
                paper_path = f"../rag/attachments/papers/{zotero_api_key}",
                user_exist = user_exits, 
                update = update
                )
            
        st.session_state["retriever"] = retriever
        response = "Let's dive into Zotero 🤿!"
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message(name = "assistant").markdown(response)
        st.session_state['db_status'] = f'<p style="color: green;"><strong>Database last updated on: {latest_time}</strong></p>'
        st.sidebar.markdown(st.session_state['db_status'], unsafe_allow_html=True)


    # User input
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message(name = "user").markdown(prompt)
        if (not openai_api_key) or (not zotero_api_key):
            st.info("Please add your API keys to continue.")
            st.stop()
        response, images = retrieve(st.session_state["retriever"], prompt)
        response = convert_to_latex(response)

        if len(images)!=0:
            response += ("\nThese images are for your reference: \n" +  
                "\n".join(['Paper Title: {}, <img width="80%" height="80%" src="data:image/jpeg;base64,{}" />'.format(image.metadata['title'], image.page_content) for image in images]))
        st.session_state["response"] = response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message(name = "assistant").markdown(response)


if __name__ == "__main__":

    main()