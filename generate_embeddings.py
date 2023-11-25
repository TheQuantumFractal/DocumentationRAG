import argparse
import pinecone
import os
from langchain.text_splitter import MarkdownTextSplitter
from langchain.vectorstores import Pinecone
from services import embedding

parser = argparse.ArgumentParser(description='Generate embeddings for a directory')
parser.add_argument('--directory', type=str, help='Path to the directory')

args = parser.parse_args()

pinecone.init(
	api_key=os.environ['PINECONE_API_KEY'],      
	environment='gcp-starter'      
)
INDEX_NAME = 'modal'

# Split markdown files into chunks of 512 tokens with 100 token overlap
markdown_splitter = MarkdownTextSplitter(chunk_size=512, chunk_overlap=100)
texts = []
for filename in os.listdir(args.directory):
    if filename.endswith('.txt'):
        with open(os.path.join(args.directory, filename), 'r') as f:
            texts.append(f.read())
documents = markdown_splitter.create_documents(texts)
Pinecone.from_documents(documents, embeddings, index_name=INDEX_NAME)
