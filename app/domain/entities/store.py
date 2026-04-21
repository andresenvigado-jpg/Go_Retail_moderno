from dataclasses import dataclass
from typing import Optional


@dataclass
class Store:
    """Entidad de dominio Tienda."""
    tienda_id: str
    nombre: str
    ciudad: str
    region: str
    formato: Optional[str] = None   # grande, mediano, pequeño, express
    clima: Optional[str] = None     # frio, calido, tropical
    zona: Optional[str] = None      # norte, sur, centro, occidente, oriente
    id: Optional[int] = None
