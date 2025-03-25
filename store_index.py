from src.utils import load_pdf,text_split,download_hugging_face_embeddings
from dotenv import load_dotenv
from pinecone import Pinecone
import os

load_dotenv()
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_API_ENV = os.environ.get('PINECONE_API_ENV')

print(PINECONE_API_ENV)
print(PINECONE_API_KEY)

extracted_data = load_pdf("./dataset/")
text_chunks = text_split(extracted_data)
embeddings = download_hugging_face_embeddings()

# Instantiate client
pc = Pinecone(api_key= PINECONE_API_KEY)
index_name="medical-chatbot-2"
index = pc.Index(name=index_name)

for i, t in zip(range(len(text_chunks)), text_chunks):
   query_result = embeddings.embed_query(t.page_content)
   index.upsert(
   vectors=[
        {
            "id": str(i),  # Convert i to a string
            "values": query_result, 
            "metadata": {"text":str(text_chunks[i].page_content)} # meta data as dic
        }
    ],
    namespace="medical-doc" 
)
