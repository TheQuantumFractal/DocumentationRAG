import argparse
import pinecone
import os
from langchain.text_splitter import MarkdownTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

parser = argparse.ArgumentParser(description='Generate embeddings for a directory')
parser.add_argument('--directory', type=str, help='Path to the directory')

args = parser.parse_args()

pinecone.init(
	api_key=os.environ['PINECONE_API_KEY'],      
	environment='gcp-starter'      
)
index_name = 'modal'
index = pinecone.Index(index_name)

embeddings = OpenAIEmbeddings()

markdown_splitter = MarkdownTextSplitter(chunk_size=512, chunk_overlap=100)
texts = []
# Go through the directory
for filename in os.listdir(args.directory):
    if filename.endswith('.txt'):
        with open(os.path.join(args.directory, filename), 'r') as f:
            texts.append(f.read())
documents = markdown_splitter.create_documents(texts)
Pinecone.from_documents(documents, embeddings, index_name=index_name)