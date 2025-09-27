# Proyecto Preguntar - Orquestación con LLM y Microservicios

Este proyecto implementa un **endpoint central llamado `preguntar`** que permite consultar funcionalidades distribuidas en diferentes microservicios.  
El flujo funciona de la siguiente manera:

1. El cliente realiza una petición al endpoint `/preguntar`.
2. Se envía una **pregunta en lenguaje natural**.
3. Un modelo de lenguaje (LLM) interpreta la pregunta y selecciona:
   - El **microservicio adecuado**.
   - El **endpoint específico** que debe ser invocado.
4. El sistema retorna la respuesta obtenida del microservicio correspondiente.

---


## 🔹 Endpoint Principal: `/preguntar`

### Método: `POST`
**Descripción:**  
Recibe una pregunta y utiliza un LLM para determinar qué microservicio y endpoint deben ser invocados.

**Ejemplo de Request:**
```json
{
  "pregunta": "¿Cuáles son los productos disponibles?"
}
```

**Ejemplo de Respuesta:**
```json
{
  "respuesta": [
    {
      "id": 1,
      "nombre": "Helado de Vainilla",
      "precio": 5000
    },
    {
      "id": 2,
      "nombre": "Helado de Chocolate",
      "precio": 6000
    }
  ]
}
```

---

## 🔹 Definición de Herramientas (Tools)

Todos los endpoints disponibles en los microservicios deben ser definidos como **herramientas (`BaseTool`)** en el archivo `main.py`.  
Cada herramienta debe contener una **descripción clara** de lo que hace, para que el LLM pueda seleccionarla correctamente.

### Ejemplo en `main.py`:

```python
from mirascope import BaseTool

class ListarProductosTool(BaseTool):
    name: str = "listar_productos"
    description: str = "Devuelve la lista de productos registrados en el microservicio de Spring Boot."

    def run(self):
        # Aquí se hace la llamada al microservicio de productos
        import requests
        response = requests.get("http://localhost:8080/productos/listarProductos")
        return response.json()
```

---

## 🔹 Ejemplo de Microservicio: Productos

En el microservicio de **Productos (Spring Boot)** existe el endpoint:

```java
@GetMapping("/listarProductos")
@Operation(summary = "Obtener todos los productos", description = "Devuelve una lista de todos los productos registrados.")
@ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Lista de productos obtenida con éxito"),
        @ApiResponse(responseCode = "500", description = "Error interno del servidor")
})
public ResponseEntity<List<Producto>> listarProductos() {
    List<Producto> lista = productoService.listar();
    return new ResponseEntity<>(lista, HttpStatus.OK);
}
```

El LLM podrá invocar este endpoint automáticamente cuando reciba una pregunta como:  
*"¿Qué productos hay disponibles?"*

---

## 🔹 Flujo General

1. El usuario pregunta algo en `/preguntar`.
2. El LLM interpreta la pregunta.
3. El LLM elige un **Tool** definido en `main.py`.
4. El Tool hace la llamada al microservicio correspondiente (ejemplo: Spring Boot).
5. El resultado se devuelve al usuario en formato JSON.

---

## 🔹 Requisitos

- Python 3.10+
- FastAPI
- Mirascope
- Requests
- Spring Boot (para los microservicios)

---

# Comandos para iniciar el proyecto

-- archivo .env que debe de tener esta variable
GOOGLE_API_KEY=xxxx

--crear entorno virtual
python -m venv .venv

--activar entorno
.venv\Scripts\Activate.ps1

-- instalar dependencias de un txt
pip install -r requirements.txt

--ejecutar servidor
python server.py

--ejecutar cliente
fastapi dev cliente.py

-- para guardar las librerias que se
pip freeze > requirements.txt