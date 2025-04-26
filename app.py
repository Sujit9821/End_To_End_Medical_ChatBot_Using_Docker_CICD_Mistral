from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uvicorn

# Load env vars
load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variable for QA model
qa = None

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/test-bg")
async def test_background():
    return FileResponse("static/background.jpg")

@app.post("/get")
async def get_answer(msg: str = Form(...)):
    global qa
    if qa is None:
        return JSONResponse({"error": "Model is loading, please try again later."}, status_code=503)
    result = qa.invoke({"query": msg})
    return {"response": result["result"]}

@app.on_event("startup")
async def startup_event():
    """
    Heavy initialization happens here.
    """
    global qa
    from huggingface_hub import hf_hub_download, login
    from src.utils import download_hugging_face_embeddings
    from src.prompt import prompt_template
    from langchain_pinecone import Pinecone
    from langchain_community.llms import CTransformers
    from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA
    import pinecone

    # Hugging Face login
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not found.")
    login(token=HF_TOKEN)

    # Download model if missing
    BASE_DIR = os.path.dirname(__file__)
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q5_K_M.gguf"
    MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(MODEL_PATH):
        hf_hub_download(
            repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
            filename=MODEL_FILENAME,
            local_dir=MODEL_DIR,
            token=HF_TOKEN
        )

    # Setup Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)
    index_name = "medical-chatbot-index"

    if index_name not in pc.list_indexes().names():
        pc.create_index(name=index_name, dimension=384, metric="cosine")
    index = pc.Index(index_name)

    # Setup embeddings and QA chain
    embeddings = download_hugging_face_embeddings()
    docsearch = Pinecone.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
        text_key="text",
        namespace="medical-doc"
    )

    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    llm = CTransformers(
        model=MODEL_PATH,
        model_type="mistral",
        config={"max_new_tokens": 512, "temperature": 0.3, "top_p": 0.9}
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=docsearch.as_retriever(search_kwargs={"k": 2}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
