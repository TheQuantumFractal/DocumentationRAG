import argparse
import pinecone
import os
from langchain.text_splitter import MarkdownTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.llms import Modal

parser = argparse.ArgumentParser(description='Generate an answer to given user query')
parser.add_argument('--query', type=str, help='User query')

args = parser.parse_args()

pinecone.init(
	api_key=os.environ['PINECONE_API_KEY'],      
	environment='gcp-starter'      
)
model = Modal(endpoint_url=os.environ['MODAL_ENDPOINT_URL'])
index_name = 'modal'
index = pinecone.Index(index_name)

embeddings = OpenAIEmbeddings()
docsearch = Pinecone.from_existing_index(index_name, embeddings)

template = """You are a helpful assistant, below is a query from a user and
some relevant contexts. Answer the question given the information in those
contexts. If you cannot find the answer to the question, say "I don't know".

Contexts:
{context}

Query: {question}

Answer: """

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

system_message_prompt = SystemMessagePromptTemplate.from_template(template)
prompt = ChatPromptTemplate.from_messages([system_message_prompt])
retriever = docsearch.as_retriever(search_kwargs={'k': 6})
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
print("Answer:", chain.invoke(args.query))