import argparse
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from services import model, embeddings, docsearch

parser = argparse.ArgumentParser(description='Generate an answer to given user query')
parser.add_argument('--query', type=str, help='User query')

args = parser.parse_args()

template = """You are a helpful assistant who answers questions regarding the Modal python library.
Below is a question about Modal from a user and some relevant contexts from Modal documentation.
Answer the question given only the information in those contexts. If you cannot find the answer to the question, say "I don't know".

Contexts:
{context}

Question: {question}

Answer: """

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

# Run the RAG model via LangChain
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
prompt = ChatPromptTemplate.from_messages([system_message_prompt])
retriever = docsearch.as_retriever(search_kwargs={'k': 6})
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
print("Answer:", chain.invoke(args.query).split("Answer:")[-1])
