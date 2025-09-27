from fastapi import FastAPI
from pydantic import BaseModel
import requests
from mirascope import llm, BaseTool
from dotenv import load_dotenv
import os

# --- 0. Cargar variables de entorno ---
load_dotenv()
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# --- 1. Definición de las tools ---
class ListarPersonasTool(BaseTool):
    """Devuelve la lista de personas llamando al microservicio de personas."""
    def call(self) -> str:
        resp = requests.get("https://randomuser.me/api/")
        return resp.json() 

class ListarProductosTool(BaseTool):
    """Devuelve la lista de productos llamando al microservicio de productos."""
    def call(self) -> str:
        resp = requests.get("https://fakestoreapi.com/products")
        return resp.json() 
    
class SaludarTool(BaseTool):
    """Devuelve un saludo amistoso"""
    def call(self) -> str:
        resp = requests.get("http://127.0.0.1:8000/")
        return resp.json() 


# --- 2. LLM con herramientas ---
@llm.call(
    "google",
    model="gemini-2.5-pro",
    tools=[ListarPersonasTool, ListarProductosTool, SaludarTool],
)
def get_user_intent(query: str):
    """
    Eres un asistente que debe decidir si la consulta del usuario
    se refiere a 'personas' o 'productos'. Usa la herramienta adecuada.
    """
    return query


# --- 3. FastAPI Models ---
class Pregunta(BaseModel):
    texto: str


# --- 4. Endpoints ---
@app.get("/")
def read_root():
    return {"Hello": "Valentina"}

@app.post("/preguntar")
def preguntar(pregunta: Pregunta):
    response = get_user_intent(pregunta.texto)

    if response.tool:
        # Ejecutar la tool seleccionada
        tool_result = response.tool.call()
        return tool_result
    else:
        return response.content
