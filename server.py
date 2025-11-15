import requests
from mcp.server.fastmcp import FastMCP, Context

def log_mcp(msg):
    with open("mcp_debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

mcp = FastMCP("MicroserviceServer")

@mcp.tool()
async def listar_productos_spring(ctx: Context):
    """Obtiene todos los productos desde el microservicio de Spring Boot."""
    resp = requests.get("http://localhost:8080/api/productos/listarProductos")

    if resp.status_code == 200:
        return [{"type": "json", "structured": resp.json()}]
    return [{"type": "json", "structured": {"error": "No se pudieron obtener los productos"}}]

@mcp.tool()
async def buscar_producto_por_id(ctx: Context, id: int):
    """Busca un producto por ID en el microservicio de Spring Boot."""
    resp = requests.get(f"http://localhost:8080/api/productos/buscarPorId/{id}")
    if resp.status_code == 200:
        return [{"type": "json", "structured": resp.json()}]
    return [{"type": "json", "structured": {"error": "Producto no encontrado"}}]


@mcp.tool()
async def buscar_producto_por_nombre(ctx: Context, nombre: str):
    """Busca un producto por nombre exacto en el microservicio de Spring Boot."""
    resp = requests.get(f"http://localhost:8080/api/productos/buscarPorNombre", params={"nombre": nombre})
    if resp.status_code == 200:
        return [{"type": "json", "structured": resp.json()}]
    return [{"type": "json", "structured": {"error": "Producto no encontrado"}}]


@mcp.tool()
async def buscar_producto_por_precio(ctx: Context, precio: float, condicion: str):
    """Busca productos por precio con una condición (mayor, menor o igual) en el microservicio de Spring Boot."""
    resp = requests.get(
        f"http://localhost:8080/api/productos/buscarPorPrecio",
        params={"precio": precio, "condicion": condicion}
    )
    if resp.status_code == 200:
        return [{"type": "json", "structured": resp.json()}]
    elif resp.status_code == 400:
        return [{"type": "json", "structured": {"error": "Condición inválida"}}]
    return [{"type": "json", "structured": {"error": "No se encontraron productos"}}]



@mcp.tool()
async def crear_producto_por_nombre_y_precio(ctx: Context, nombre: str, precio: float):
    log_mcp(f"Llamada a crear_producto con nombre={nombre}, precio={precio}")
    url = "http://localhost:8080/api/productos/crear"
    data = {"nombre": nombre, "precio": precio}
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    try:
        log_mcp(f"Payload enviado: {data}")
        resp = requests.post(url, json=data, headers=headers)
        log_mcp(f"Status code: {resp.status_code}")
        log_mcp(f"Response headers: {resp.headers}")
        log_mcp(f"Response body: {resp.text}")
        if resp.status_code in (200, 201):
            try:
                return [{"type": "json", "structured": resp.json()}]
            except Exception:
                return [{"type": "json", "structured": {"raw_body": resp.text}}]
        elif resp.status_code == 400:
            return [{"type": "json", "structured": {"error": "Datos inválidos", "detalle": resp.text}}]
        else:
            return [{"type": "json", "structured": {"error": f"Error {resp.status_code}", "detalle": resp.text}}]
    except Exception as e:
        log_mcp(f"Error de conexión: {str(e)}")
        return [{"type": "json", "structured": {"error": "Error de conexión", "detalle": str(e)}}]


if __name__ == "__main__":
    print("Servidor MCP para microservicios iniciado...")
    mcp.run()
