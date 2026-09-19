"""Cliente HTTP para customer_api (clientes, reembolsos y reseteo de contraseña).

Variables de entorno:
    CUSTOMER_API_URL   URL base de customer_api (default: http://127.0.0.1:8000).
"""

import os

import httpx

CUSTOMER_API_URL = os.getenv("CUSTOMER_API_URL", "http://127.0.0.1:8000")


async def buscar_cliente_por_email(email: str) -> dict | None:
    """Busca en customer_api el cliente cuyo correo coincide con el dado.

    Args:
        email: Correo electrónico del cliente a buscar.

    Returns:
        dict | None: Datos del cliente si existe, o None si no se encontró.
    """

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{CUSTOMER_API_URL}/api/customers/", params={"email":email})
        response.raise_for_status()
    clientes = response.json()
    return clientes[0] if clientes else None


async def crear_reintegro(customer_id: int, monto: float, motivo: str) -> dict:
    """Registra un reembolso para un cliente en customer_api.

    Args:
        customer_id: Id del cliente al que se le asigna el reembolso.
        monto: Monto del reembolso.
        motivo: Motivo del reembolso.

    Returns:
        dict: Reembolso creado (incluye id, customer, amount, reason, created_at).
    """

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{CUSTOMER_API_URL}/api/refunds/",
            json={"customer": customer_id, "amount": f"{monto:.2f}", "reason": motivo}
        )
        response.raise_for_status()

    return response.json()


async def resetear_contrasena(customer_id: int) -> dict:
    """Solicita a customer_api el reseteo de contraseña de un cliente.

    Args:
        customer_id: Id del cliente al que se le resetea la contraseña.

    Returns:
        dict: Respuesta de customer_api con el enlace de reseteo (reset_link).
    """
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{CUSTOMER_API_URL}/api/customers/{customer_id}/reset_password/"
        )
        response.raise_for_status()

    return response.json()
