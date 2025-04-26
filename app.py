from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.utils import download_hugging_face_embeddings
from src.prompt import prompt_template
from langchain_pinecone import Pinecone
from langchain_community.llms import CTransformers  
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download, login
import pinecone
import os
import uvicorn

# Load environment variables
load_dotenv()

# Authenticate Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file.")
login(token=HF_TOKEN)

# Model path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)
os.makedirs(MODEL_DIR, exist_ok=True)

# Download model if not present
if not os.path.exists(MODEL_PATH):
    print(f"Downloading model to {MODEL_PATH}...")
    MODEL_PATH = hf_hub_download(
        repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        filename=MODEL_FILENAME,
        local_dir=MODEL_DIR,
        token=HF_TOKEN
    )
    print(f"✅ Model downloaded at {MODEL_PATH}")

# Setup Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)
index_name = "medical-chatbot-index"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(index_name)

# Embedding and Retriever
embeddings = download_hugging_face_embeddings()
docsearch = Pinecone.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
    text_key="text",
    namespace="medical-doc"
)

# Setup LangChain QA Chain
PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
llm = CTransformers(
    model=MODEL_PATH,
    model_type="mistral",
    config={
        "max_new_tokens": 512,
        "temperature": 0.3,
        "top_p": 0.9
    }
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=docsearch.as_retriever(search_kwargs={"k": 2}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# FastAPI App
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/test-bg")
async def test_background():
    return FileResponse("/app/static/background.jpg")

@app.post("/get")
async def get_answer(msg: str = Form(...)):
    result = qa.invoke({"query": msg})
    return {"response": result["result"]}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
