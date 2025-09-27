import requests
from mcp.server.fastmcp import FastMCP, Context

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


if __name__ == "__main__":
    print("Servidor MCP para microservicios iniciado...")
    mcp.run()
