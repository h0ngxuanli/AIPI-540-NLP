# Multi-modal Local File Search & Recommendation Engine 

## Resources
- Youtube Link: https://www.youtube.com/watch?v=N9rPOchEAhc&t=1s
- Deployed product: still struggling...
- Slides: https://docs.google.com/presentation/d/1cNkXGMtD9vlQtVOGmrhtY7usKhHPov7ZltFdm4uy_QM/edit?usp=sharing

## Reference
- [st-chat-message](https://github.com/undo76/st-chat-message) , which connects Next.js front-end code with python through streamlit component. ZotoMind's interface is based on this repo.

## Introduction

This project aims to connect all forms of information(e.g. equations, tables, figures) inside your own Zotero collection. Different from previous LLMs-based paper reading web applications, ZotoMind is naturally integrated with Zotero through encoding the pdf files into markdown texts, tables, images without information loss. With ZotoMind, any forms of relevant information can be retrieved to answer users' queries.

![alt text](<figures/name.png>)

## Features
- Unique Database: you can create independent retrievers with different Zotero API keys.
- Information Retrieval: various forms of relevant information can be accurately retrieved through multi-vector retrieval provided by LangChain.
- User-friendly Interface: the chatbox supports latex, tables, images and other forms of media.

## Repo Structure

Overview:
- `interface`: Contains front-end .js code rendering chatbox and interface streamlit code
- `data`: Contains papers pulled from Zotero with API key
- `model`: Contains deployed Nougat
- `rag`: Contains the code used for building RAG pipeline and the saved retriever (vector database & document database)



```
ZotoMind/     
│
├── rag/                              
│   └── utils/   
│       ├── inference_utils.py
│       ├── pdf_processor.py
│       ├── rag_utils.py
│       ├── summary_utils.py
│       └── zoto_utils.py
│   ├── extract_wikidata.ipynb          
│   └── rag_pipeline.py                    
│
├── interface/                            
│   ├── message_ui/  
│       └── st_chat_message/
│           └── frontend/               
│   ├── main.py                      
│   └── requirements.txt                        
│
├── model/
│   └── nougat
│       └── handler.py             
├──data/                                                      
│   └── papers/     
│       └── article_{paper_key}.pdf                    
│
├── README.md
│
├── requirements.txt
│
└── .gitignore

```


## Overall Architecture

![alt text](<figures/image.png>)

## How to use
1. Clone the repository
```bash
git clone git@github.com:h0ngxuanli/AIPI-540-NLP.git
```
2. Creat a virtual environment(using conda in this case) for the project
```bash
conda create -n zotomind
conda activate zotomind
```
3. Install the required packages
```bash
pip install -r requirements.txt
```
4. Enter the interface dir
```bash
cd interface
```
5. Run the streamlit app, the development environment will be automatically created for Node.js
```bash
streamlit run main.py
```

## Limitations

- Weak at retrieving tabels and figures: images are encoded independent from context

- Computational heavy: Nougat + YOLO + LLMs

- Unstable Latex equation rendering: a missing backslash retrieved by LLMs could cause the error latex display




