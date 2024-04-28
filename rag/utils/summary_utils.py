# Image summarizer

import base64
import os
from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_text_splitters import MarkdownHeaderTextSplitter
from openai import OpenAI
import numpy as np

class ImageSummarizer:

    def __init__(self, image_path, context) -> None:
        self.image_path = image_path
        self.prompt = f"""
You are an assistant tasked with summarizing images for paper retrieval.
These summaries will be embedded and used to retrieve the relevant experiments.
The image can be either a figure or a table in the paper that illustrates experimental results.
Give a concise and precise summary of the image that is well optimized for retrieval based on the following paper context:
{context}
"""

    def base64_encode_image(self):
        with open(self.image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def summarize(self, prompt = None):
        base64_image_data = self.base64_encode_image()
        chat = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=1000)

        response = chat.invoke(
            [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt if prompt else self.prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image_data}"},
                        },
                    ]
                )
            ]
        )
        return base64_image_data, response.content
    
def summarize_figure_table(images_path, paper_context):
    figure_data_list = []
    figure_summary_list = []

    table_data_list = []
    table_summary_list = []

    print(len(os.listdir(images_path)))
    for img_file in sorted(os.listdir(images_path)):
        if img_file.endswith(".jpg"):
            
            summarizer = ImageSummarizer(os.path.join(images_path, img_file), context=paper_context)
            try:
                data, summary = summarizer.summarize()
            except:
                print("Error when Summarizing with GPT")
                print("*"*20)
                continue


            if img_file.startswith("table"):
                table_data_list.append(data)
                table_summary_list.append(summary)
            elif img_file.startswith("figure"):
                figure_data_list.append(data)
                figure_summary_list.append(summary)
    return table_data_list, table_summary_list, figure_data_list, figure_summary_list


def summarize_text(texts):
    prompt_text = """
    You are responsible for concisely summarizing the text chunk, if there are latex equations included in the text chunk, please explain them:

    {element}
    """
    prompt = ChatPromptTemplate.from_template(prompt_text)
    summarize_chain = {"element": lambda x: x} | prompt | ChatOpenAI(temperature=0, model="gpt-3.5-turbo") | StrOutputParser()
    text_summaries = summarize_chain.batch(texts, {"max_concurrency": 5})
    return text_summaries


def summarize_paper_context(text, model="gpt-3.5-turbo-1106", max_tokens=150):
    client = OpenAI()
    response = client.chat.completions.create(
        model = model,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": f"Please summarize the following paper to provide a context for readers:\n\n" + text}
        ],
        max_tokens=max_tokens,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()



def markdown_split(texts):

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    # md_header_splits = markdown_splitter.split_text(markdown_document)
    # md_header_splits
    sub_docs = []
    for i, doc in enumerate(texts):
        _sub_docs = markdown_splitter.split_text(doc)
        for docs in _sub_docs:
            sub_docs.append(docs.page_content)
    return sub_docs


def extract_paper_title(texts):
    if len(texts) == 0:
        return "No Title"
    else:
        title = np.array(texts[0].split("\n"))
        title = title[title != ""][0]

        title = np.array(title.split("#"))
        title = title[title != ""][0]
        return title
