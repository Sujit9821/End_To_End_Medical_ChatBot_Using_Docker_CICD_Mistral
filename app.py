from flask import Flask, render_template, jsonify, request
from src.utils import download_hugging_face_embeddings
from langchain_pinecone import Pinecone
from langchain_community.llms import CTransformers
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download, login
import pinecone
import os

# Load environment variables
load_dotenv()

# Hugging Face authentication (add your token to .env or hardcode it here temporarily)
HF_TOKEN = os.getenv("HF_TOKEN")  # Ensure HF_TOKEN is set in your .env file
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file. Please set it to your Hugging Face access token.")
login(token=HF_TOKEN)  # Authenticate with Hugging Face

# Define model details
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"  # Correct filename
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

# Ensure models directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Download model if not present
if not os.path.exists(MODEL_PATH):
    print(f"Downloading model to {MODEL_PATH}...")
    MODEL_PATH = hf_hub_download(
        repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",  # Correct repo_id
        filename=MODEL_FILENAME,
        local_dir=MODEL_DIR,
        token=HF_TOKEN  # Pass the token explicitly
    )
    print(f"Model downloaded to {MODEL_PATH}")

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

index_name = "medical-chatbot-index"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric='cosine',
        spec=pinecone.ServerlessSpec(cloud='aws', region='us-east-1')
    )

index = pc.Index(index_name)

# Initialize Embeddings
embeddings = download_hugging_face_embeddings()

docsearch = Pinecone.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
    text_key="text",
    namespace="medical-doc"
)

# Define Prompt Template (refined for concise answers)
prompt_template = """
Given the following context: {context}
Answer the question directly and concisely: {question}
Provide only the requested information, no additional questions or content.
"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
chain_type_kwargs = {"prompt": PROMPT}

# Initialize LLM (Mistral-7B-Instruct)
llm = CTransformers(
    model=MODEL_PATH,
    model_type="mistral",
    config={
        'max_new_tokens': 512,
        'temperature': 0.3,
        'top_p': 0.9
    }
)

# Create Retrieval Chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docsearch.as_retriever(search_kwargs={'k': 2}),
    return_source_documents=True,
    chain_type_kwargs=chain_type_kwargs
)

# Initialize Flask App
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('chat.html')

@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    print(input)
    result = qa.invoke({"query": input})
    print("Response:", result["result"])
    return str(result["result"])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True,use_reloader=False)