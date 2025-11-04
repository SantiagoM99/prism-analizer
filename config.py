"""
Configuración del analizador de proyectos LLM.

Este módulo contiene la configuración necesaria para procesar
entregas de proyectos estudiantiles siguiendo una estructura convencional.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class EntregaConfig:
    """
    Configuración para una entrega específica de proyectos.
    
    Estructura esperada de directorios:
    ./entregas/entrega{N}/
      ├── enunciado.md
      ├── rubrica.md
      ├── proyectos/
      ├── calificaciones.csv (opcional)
      └── resultados/  (se crea automáticamente)
    
    Attributes:
        numero_entrega: Número identificador de la entrega (1, 2, 3, etc.)
        base_dir: Directorio base donde están todas las entregas
        model_name: Nombre del modelo de Gemini a utilizar
        temperature: Temperatura para la generación (0.0 - 1.0)
        max_retries: Número máximo de reintentos en caso de error
    """
    numero_entrega: int
    base_dir: Path = Path("./entregas")
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.1
    max_retries: int = 3
    
    def __post_init__(self):
        """Construye rutas y valida estructura de directorios."""
        # Construir rutas automáticamente
        self.entrega_dir = self.base_dir / f"entrega{self.numero_entrega}"
        self.enunciado_path = self.entrega_dir / "enunciado.md"
        self.rubrica_path = self.entrega_dir / "rubrica.md"
        self.proyectos_dir = self.entrega_dir / "proyectos"
        self.output_dir = self.entrega_dir / "resultados"
        self.calificaciones_csv_path = self.entrega_dir / "calificaciones.csv"
        
        # Validar que archivos requeridos existan
        if not self.enunciado_path.exists():
            raise FileNotFoundError(f"Enunciado no encontrado: {self.enunciado_path}")
        if not self.rubrica_path.exists():
            raise FileNotFoundError(f"Rúbrica no encontrada: {self.rubrica_path}")
        if not self.proyectos_dir.exists():
            raise FileNotFoundError(f"Directorio de proyectos no encontrado: {self.proyectos_dir}")
        
        # CSV de calificaciones es opcional - solo verificar si existe
        if not self.calificaciones_csv_path.exists():
            self.calificaciones_csv_path = None
        
        # Crear estructura de output
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "fase1_extracciones").mkdir(exist_ok=True)
        (self.output_dir / "fase2_consolidado").mkdir(exist_ok=True)
        (self.output_dir / "fase3_calificaciones").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)


def get_config(numero_entrega: int, **kwargs) -> EntregaConfig:
    """
    Crea configuración para una entrega específica.
    
    Args:
        numero_entrega: Número de la entrega
        **kwargs: Parámetros opcionales para sobrescribir defaults
                  (base_dir, model_name, temperature, max_retries)
    
    Returns:
        EntregaConfig configurada y validada
    
    Example:
        # Uso básico
        config = get_config(1)
        
        # Con personalización
        config = get_config(2, model_name="gemini-pro", temperature=0.2)
    """
    return EntregaConfig(numero_entrega=numero_entrega, **kwargs)