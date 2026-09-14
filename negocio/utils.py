
COSTO_DIARIO = 2160

def calcular_reintegro(dias_sin_servicio: int, indice_malestar: float) -> dict:
    """Calcula el reintegro que le corresponde a un cliente por días sin servicio.

    El monto es: días sin servicio * costo diario del servicio * índice de
    insatisfacción del cliente.

    Args:
        dias_sin_servicio: Cantidad de días que el cliente estuvo sin servicio.
        indice_malestar: Índice de insatisfacción del cliente, de 1.0 (cliente
            tranquilo) a 2.0 (cliente muy molesto), estimado según la forma en
            que se expresa el cliente.

    Returns:
        dict: Detalle del cálculo con los días, el costo diario, el índice
            aplicado y el monto total del reintegro.
    """
    if dias_sin_servicio <= 0:
        raise ValueError("Los días sin servicio deben ser un número positivo.")

    # Acotamos el índice al rango válido para evitar reintegros desmedidos.
    indice = min(max(float(indice_malestar), 1.0), 2.0)

    monto = dias_sin_servicio * COSTO_DIARIO * indice

    print(
        f"[herramienta] calcular_reintegro -> {dias_sin_servicio} día(s) x "
        f"${COSTO_DIARIO} x índice {indice} = ${monto:,.2f}"
    )

    return {
        "dias_sin_servicio": dias_sin_servicio,
        "costo_diario": COSTO_DIARIO,
        "indice_malestar": indice,
        "monto_reintegro": round(monto, 2),
    }


def recuperar_contrasena(email: str) -> dict:
    """Inicia el recupero de contraseña enviando un mail a la casilla del cliente.

    Args:
        email: Casilla de correo del cliente, donde se envía el enlace de
            recuperación.

    Returns:
        dict: Confirmación del envío del correo de recuperación.
    """
    if "@" not in email:
        raise ValueError("El correo electrónico no es válido.")

    print(
        f"[herramienta] recuperar_contrasena -> Se ha enviado un mail a la "
        f"casilla {email} con las instrucciones para restablecer la contraseña."
    )

    return {"email": email, "estado": "mail de recuperación enviado"}
