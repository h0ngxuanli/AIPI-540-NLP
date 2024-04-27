import json
import sqlite3
from typing import Tuple, Iterator
from typing import Sequence, List, Optional
import uuid
import base64
from IPython.display import HTML, display

from langchain.schema.document import Document
from langchain.schema import BaseStore
from langchain.schema.messages import HumanMessage
from pypika import Query, Table, Field, Column


class ChromaStore(BaseStore[str, bytes]):

    def __init__(self, path, table_name):
        self.connection = sqlite3.connect('{path}/chroma.sqlite3'.format(path=path), check_same_thread=False)
        self.table = Table(table_name)
        self.id_column = Field('id')
        self.data_column = Field('data')
        self._create_table()

    def _create_table(self):
        id_column = Column('id', 'VARCHAR(50)', nullable=False)
        data_column = Column('data', 'VARCHAR(2500)', nullable=False)
        create_table_query = Query.create_table(self.table).columns(id_column, data_column).if_not_exists()
        cursor = self.connection.cursor()
        cursor.execute(create_table_query.get_sql())
        cursor.close()

    def mget(self, keys: Sequence[str]) -> List[Optional[bytes]]:
        select_query = Query.from_(self.table).select(self.data_column).where(self.id_column.isin(keys))

        cursor = self.connection.cursor()
        cursor.execute(select_query.get_sql())
        results = cursor.fetchall()

        cursor.close()

        data_list = []
        for result in results:
            if result[0] is not None:
                data_list.append(json.loads(result[0]).encode("utf-8"))
            else:
                data_list.append(None)

        return data_list

    def mset(self, key_value_pairs: Sequence[Tuple[int, bytes]]) -> None:
        insert_queries = []
        for key, value in key_value_pairs:
            insert_query = Query.into(self.table).columns(self.id_column, self.data_column).insert(key, json.dumps(value.decode('utf-8')))
            insert_queries.append(insert_query)

        cursor = self.connection.cursor()
        for query in insert_queries:
            cursor.execute(query.get_sql())

        self.connection.commit()
        cursor.close()

    def mdelete(self, keys: Sequence[int]) -> None:
        delete_query = Query.from_(self.table).delete().where(self.id_column.isin(keys))
        cursor = self.connection.cursor()
        cursor.execute(delete_query.get_sql())
        self.connection.commit()
        cursor.close()

    def yield_keys(self, prefix: Optional[str] = None) -> Iterator[str]:
        select_query = Query.from_(self.table).select(self.id_column)
        if prefix:
            select_query = select_query.where(self.id_column.like(f'{prefix}%'))

        cursor = self.connection.cursor()
        cursor.execute(select_query.get_sql())

        for row in cursor.fetchall():
            yield row[0]
        cursor.close()


def add_elements(retriever, elements, summaries, id_key, title):
    doc_ids = [str(uuid.uuid4()) for _ in elements]
    summary_elements = [
                Document(page_content=s, metadata={id_key: doc_ids[i], "title":title})
                for i, s in enumerate(summaries)
            ]
    elements = [
                Document(page_content=s, metadata={id_key: doc_ids[i], "title":title})
                for i, s in enumerate(elements)
            ]
    retriever.vectorstore.add_documents(summary_elements)
    retriever.docstore.mset(list(zip(doc_ids, elements)))

    return retriever


def plt_img_base64(img_base64):
    display(HTML(f'<img src="data:image/jpeg;base64,{img_base64}" />'))

def is_image_data(b64data):
    """
    Check if the base64 data is an image by looking at the start of the data
    """
    image_signatures = {
        b"\xFF\xD8\xFF": "jpg",
        b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A": "png",
        b"\x47\x49\x46\x38": "gif",
        b"\x52\x49\x46\x46": "webp",
    }
    try:
        header = base64.b64decode(b64data)[:8]  # Decode and get the first 8 bytes
        for sig, format in image_signatures.items():
            if header.startswith(sig):
                return True
        return False
    except Exception:
        return False

def split_image_text_types(docs):
    """
    Split base64-encoded images and texts
    """
    b64_images = []
    texts = []
    for doc in docs:
        # Check if the document is of type Document and extract page_content if so
        if isinstance(doc, Document):
            doc = doc.page_content

        if is_image_data(doc):
            b64_images.append(doc)
        else:
            texts.append(doc)
    # print(texts)
    return {"images": b64_images, "texts": texts}


def img_prompt_func(data_dict):

    messages = []
    # Adding image(s) to the messages if present
    if data_dict["context"]["images"]:
        for image in data_dict["context"]["images"]:
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }
            messages.append(image_message)

    # Adding texts to the messages
    formatted_texts = "\n".join(data_dict["context"]["texts"])

    text_message = {
        "type": "text",
        "text": (
            "You are an expert in retrieving information from documents CONTEXT.\n"
            "Answer the users' QUESTION using the given documents CONTEXT.\n"
            "Keep your answer ground in the facts of the documents CONTEXT.\n"
            "The ANSWER could be text, tables, figures or latex equations.\n"
            f"CONTEXT: {formatted_texts}"
            f"QUESTION: {data_dict['question']}\n\n"
            "ANSWER:\n"
            
        ),
    }
    messages.append(text_message)
    return [HumanMessage(content=messages)]