FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3 python3-pip

USER root 


# install Nodejs
WORKDIR /Node
COPY node-v20.11.0-linux-x64.tar.xz .
# 将 tar.xz 压缩文件转成 node-v10.15.0-linux-arm64.tar
RUN xz -d node-v20.11.0-linux-x64.tar.xz
# 再用 tar xvf node-v10.15.0-linux-arm64.tar  解压缩文件
RUN tar -xvf node-v20.11.0-linux-x64.tar
# 可修改名字
RUN mv node-v20.11.0-linux-x64 nodejs
RUN ln -s /Node/nodejs/bin/node /usr/bin/node
RUN ln -s /Node/nodejs/bin/npm /usr/bin/npm


# USER wang 
WORKDIR /AIPI-540-NLP
# copy frontend
COPY ./interface/message_ui/st_chat_message/frontend/out /AIPI-540-NLP
COPY ./interface/requirements.txt ./interface/requirements.txt

WORKDIR /AIPI-540-NLP/interface
RUN pip3 install -r requirements.txt


WORKDIR  /AIPI-540-NLP
COPY ./rag ./rag 
COPY ./interface/main.py ./interface/main.py 

ENTRYPOINT [ "streamlit", "run","/AIPI-540-NLP/interface/main.py" ] 

# docker build -t zotomind .
