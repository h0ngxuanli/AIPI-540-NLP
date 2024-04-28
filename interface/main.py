import warnings
warnings.filterwarnings("ignore")

import subprocess
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
# from message_ui.st_chat_message import message
# from st_chat_message import message
from rag.rag_pipeline import build_retriever, retrieve
from rag.utils.zoto_utils import initialize_zotero
from rag.utils.zoto_utils import pull_paper_parallelized, initialize_zotero, get_paper_keys, get_meta_data
from rag.utils.inference_utils import convert_to_latex
import subprocess
import streamlit as st


def main():

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
        # message(message_text["content"], is_user = True if message_text["role"] == "user" else False, key = id)
        st.chat_message(name = "user" if message_text["role"] == "user" else "assistant").markdown(message_text["content"])
            
            


    with open("interface/sidebar/styles.md", "r") as styles_file:
        styles_content = styles_file.read()
    st.write(styles_content, unsafe_allow_html=True)


    # Set API keys
    st.sidebar.header('Zotero API Key🔑')
    zotero_api_key = st.sidebar.text_input('', key='Zotero Key', type="password")
    if zotero_api_key:
        st.sidebar.success('Zotero API Key entered!')

        
    os.environ['PINECONE_API_KEY'] = "5a727c08-72c8-4031-8d55-7b268c06c443"

    st.sidebar.header('Zotero Library ID🗝️')
    library_id = st.sidebar.text_input('', key='Zotero Libr', type="password")
    if library_id:
        st.sidebar.success('Zotero Library ID entered!')


    with st.sidebar:
        "[Get Your Zotero API Key & Library ID](https://www.zotero.org/settings/keys)"

    st.sidebar.header('GPT-4 Key🔑')
    openai_api_key = st.sidebar.text_input('', key='GPT-4 Key', type="password")
    if openai_api_key:
        st.sidebar.success('OpenAI API Key entered!')
        os.environ["OPENAI_API_KEY"] = openai_api_key

    if st.sidebar.button("Check Database"):
        if library_id:
            library_id = int(library_id)

        # check whether exist data
        if os.path.exists(f"./rag/attachments/{library_id}/"):
            with open(f"./rag/attachments/{library_id}/latest_time.txt", 'r') as file:
                # Read the contents of the file
                latest_time =  file.read()
            latest_time = datetime.strptime(latest_time, '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d")
            st.session_state['db_status'] = f'<p style="color: green;"><strong>Database last updated on: {latest_time}</strong></p>'
        else:
            st.session_state['db_status'] = '<p style="color: red;"><strong>You have not built your database</strong></p>'
        st.sidebar.markdown(st.session_state['db_status'], unsafe_allow_html=True)



    if st.sidebar.button("Updating Database") & (zotero_api_key is not None) & (library_id is not None):
        st.session_state.messages.append({"role": "assistant", "content": "Start building database for your Zotero collections 💡 ... "})
        st.chat_message(name = "assistant").markdown("Start building database for your Zotero collections 💡 ... ")
        # message("Start building database for your Zotero collections 💡 ... ", is_user = False)




        zot = initialize_zotero(library_id = library_id, zotero_api_key = zotero_api_key, api_key = zotero_api_key)#"3WYiWAu8bLIX6pIo6IBhYkJs"

        if os.path.exists(f"./rag/attachments/{library_id}/") and len(os.listdir(f"./rag/attachments/{library_id}/"))!=0:
            
            with open(f"./rag/attachments/{library_id}/latest_time.txt", 'r') as file:
                # Read the contents of the file
                latest_time =  file.read()

            try:
                # shutil.rmtree(f"./rag/attachments/{library_id}/")
                latest_time = pull_paper_parallelized(zot, 
                                        file_path = f"./rag/attachments/{library_id}/", 
                                        num_processes = 5, 
                                        latest_time = latest_time)
            except:
                latest_time = latest_time 
        
        else:
            os.mkdir(f"./rag/attachments/{library_id}/")
            latest_time = pull_paper_parallelized(zot, 
                                    file_path = f"./rag/attachments/{library_id}/", 
                                    num_processes = 5, 
                                    latest_time = None)
            
        # update latest time
        with open(f"./rag/attachments/{library_id}/latest_time.txt", 'w') as file:
            # Write the string to the file
            file.write(latest_time)
        
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

        st.session_state.messages.append({"role": "assistant", "content": markdown_string})
        # message(markdown_string, is_user = False)
        st.chat_message(name = "assistant").markdown(markdown_string)

        response = "Your database is all set 🥳!"
        st.session_state.messages.append({"role": "assistant", "content": response})
        # message(response, is_user = False)
        st.chat_message(name = "assistant").markdown(response)

        st.session_state['db_status'] = f'<p style="color: green;"><strong>Database last updated on: {latest_time}</strong></p>'
        st.sidebar.markdown(st.session_state['db_status'], unsafe_allow_html=True)



    # User input
    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        # message(prompt, is_user=True)
        st.chat_message(name = "user").markdown(prompt)

        if (not openai_api_key) or (not zotero_api_key):
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        # # get retriever
        # # use already existing Vector base
        retriever = build_retriever(
                        zotero_key = "10papers", 
                        paper_path = None,
                        user_exist = True, 
                        update = False
                        )

        response, images = retrieve(retriever, prompt)
        response = convert_to_latex(response)

        if len(images)!=0:
            response += ("\nThese images are for your reference: \n" +  
                "\n".join(['Paper Title: {}, <img width="80%" height="80%" src="data:image/jpeg;base64,{}" />'.format(image.metadata['title'], image.page_content) for image in images]))


        st.session_state["response"] = response
        st.session_state.messages.append({"role": "assistant", "content": response})
        # message(st.session_state["response"], is_user=False)
        st.chat_message(name = "assistant").markdown(response)




if __name__ == "__main__":

    main()