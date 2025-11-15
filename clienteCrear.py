import asyncio
import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel
from mirascope import llm, BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import json
from fastapi.middleware.cors import CORSMiddleware

# --- 1. Cargar variables de entorno ---
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError(" Falta GOOGLE_API_KEY en el entorno. Crea un archivo .env con tu clave.")

app = FastAPI()

#permite todos los cors
origins = [
    "http://127.0.0.1:5500",  # Tu Live Server
    "http://localhost:5500",  # A veces Live Server usa localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Tools que Gemini puede elegir ---


class CrearProductoPorNombreYPrecioTool(BaseTool):
    """
    Herramienta exclusiva para CREAR, registrar, agregar, añadir o dar de alta un producto nuevo en el microservicio. 
    Usa esta herramienta SOLO cuando el usuario quiera crear, registrar, agregar, añadir o dar de alta un producto, indicando el nombre (campo 'nombre', texto) y el precio (campo 'precio', número).

    Ejemplos de frases:
      - "Crea un producto llamado banano con precio 7000"
      - "Agregar producto: nombre banano, precio 7000"
      - "Registrar producto banano, precio 7000"
      - "Quiero dar de alta el producto banano por 7000"
      - "Añade producto banano precio 7000"
      - "Voy a crear un nuevo producto: banano, 7000"
      - "Alta producto banano 7000"
      - "Crear producto"
    """
    def call(self, nombre: str, precio: float) -> str:
        return f"CrearProductoTool crear con nombre={nombre}, precio={precio}."



# --- 3. Mapeo entre nombres del LLM y nombres en el servidor ---
TOOL_NAME_MAP = {
    "CrearProductoPorNombreYPrecioTool": "crear_producto_por_nombre_y_precio"
}

# --- 4. LLM ---
@llm.call(
    "google",
    model="gemini-2.5-pro",
    tools=[CrearProductoPorNombreYPrecioTool],
)
def get_user_intent(query: str):
    return query

# --- 5. Esquema de entrada ---
class Pregunta(BaseModel):
    texto: str

def log_client(msg):
    with open("client_debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

@app.post("/debug_crear")
async def debug_crear():
    server_params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("crear_producto_por_nombre_y_precio", arguments={"nombre": "banano", "precio": 7000})
            return {"resultado": str(result)}

# --- 6. Endpoint ---
@app.post("/preguntar")
async def preguntar(pregunta: Pregunta):
    server_params = StdioServerParameters(command=sys.executable, args=["server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = get_user_intent(pregunta.texto)

            if response.tool:
                tool_call_info = response.tool.tool_call
                tool_name = tool_call_info.name
                tool_args = tool_call_info.args

                log_client(f"tool_name: {tool_name}")
                log_client(f"tool_args: {tool_args}")

                tool_name_on_server = TOOL_NAME_MAP.get(tool_name)
                if not tool_name_on_server:
                    return {"error": f"LLM devolvió una herramienta desconocida: {tool_name}"}

                result = await session.call_tool(tool_name_on_server, arguments=tool_args)
                
                if result.isError:
                    return {"error": result.content}

                # --- LOGICA DE PARSEO DE RESPUESTA DEL SERVIDOR MCP ---
                # La respuesta del servidor MCP puede venir de dos formas:
                #
                # 1. Como "structuredContent" (preferido): una lista de objetos con el atributo .structured,
                #    que puede ser un dict/list con cualquier estructura JSON válida (arreglo de objetos, objeto con arreglos, etc).
                #    Si es string, intentamos hacer json.loads en caso de que venga serializado.
                #
                # 2. Como "content", generalmente lista de TextContent, donde el texto es un string
                #    que contiene un JSON serializado (por ejemplo: '{"type": "json", "structured": [...]}' o dict anidado).
                #    En ese caso, parseamos el string, y si tiene "structured", devolvemos ese campo,
                #    que puede ser cualquier estructura JSON arbitraria.
                #
                # Esto permite recibir y retornar al frontend cualquier combinación de JSON
                # devuelta por los microservicios (arreglos de objetos, objetos anidados, etc).
                # -----------------------------------------------------

                # Caso 1: structuredContent (preferido, si la versión de MCP lo soporta)
                if result.structuredContent:
                    data = []
                    for item in result.structuredContent:
                        val = item.structured
                        if isinstance(val, str):
                            try:
                                val = json.loads(val)
                            except Exception:
                                pass
                        data.append(val)
                    if len(data) == 1:
                        return data[0]
                    return data

                # Caso 2: content como texto JSON serializado
                if result.content:
                    for c in result.content:
                        text = getattr(c, "text", None)
                        if text:
                            try:
                                obj = json.loads(text)
                                if "structured" in obj:
                                    return obj["structured"]
                                return obj
                            except Exception as e:
                                return {"error": f"Respuesta no es JSON: {text}"}
                    return {"error": "La tool devolvió content pero no texto interpretable."}

                # Si no hay nada retornable
                return {"error": "La tool no devolvió contenido estructurado ni texto."}
				
			