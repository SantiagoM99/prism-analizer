"""
Configuración del analizador de proyectos LLM.

Este módulo contiene todas las configuraciones necesarias para procesar
una entrega específica de proyectos estudiantiles.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class EntregaConfig:
    """
    Configuración para una entrega específica de proyectos.
    
    Attributes:
        numero_entrega: Número identificador de la entrega (1, 2, 3, etc.)
        enunciado_path: Ruta al archivo markdown del enunciado
        rubrica_path: Ruta al archivo markdown de la rúbrica
        proyectos_dir: Directorio conteniendo los markdowns de proyectos
        output_dir: Directorio donde se guardarán los resultados
        model_name: Nombre del modelo de Gemini a utilizar
        temperature: Temperatura para la generación (0.0 - 1.0)
        max_retries: Número máximo de reintentos en caso de error
    """
    numero_entrega: int
    enunciado_path: Path
    rubrica_path: Path
    proyectos_dir: Path
    output_dir: Path
    model_name: str = "gemini-2.5-flash-lite"
    temperature: float = 0.1  # Baja para consistencia en extracción
    max_retries: int = 3
    
    def __post_init__(self):
        """Valida que las rutas existan y crea directorios de output."""
        # Validar que archivos de entrada existan
        if not self.enunciado_path.exists():
            raise FileNotFoundError(f"Enunciado no encontrado: {self.enunciado_path}")
        if not self.rubrica_path.exists():
            raise FileNotFoundError(f"Rúbrica no encontrada: {self.rubrica_path}")
        if not self.proyectos_dir.exists():
            raise FileNotFoundError(f"Directorio de proyectos no encontrado: {self.proyectos_dir}")
        
        # Crear directorio de output si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios para organizar resultados
        (self.output_dir / "fase1_extracciones").mkdir(exist_ok=True)
        (self.output_dir / "fase2_consolidado").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)


# Ejemplo de configuración para Entrega 1
ENTREGA_1_CONFIG = EntregaConfig(
    numero_entrega=1,
    enunciado_path=Path("./entregas/entrega1/enunciado.md"),
    rubrica_path=Path("./entregas/entrega1/rubrica.md"),
    proyectos_dir=Path("./entregas/entrega1/proyectos"),
    output_dir=Path("./entregas/entrega1/resultados")
)


def get_config_for_entrega(numero: int) -> EntregaConfig:
    """
    Retorna la configuración para una entrega específica.
    
    Args:
        numero: Número de la entrega
        
    Returns:
        EntregaConfig correspondiente
        
    Raises:
        ValueError: Si no existe configuración para ese número de entrega
    """
    configs = {
        1: ENTREGA_1_CONFIG,
        # Agregar más entregas según sea necesario
        # 2: ENTREGA_2_CONFIG,
        # 3: ENTREGA_3_CONFIG,
    }
    
    if numero not in configs:
        raise ValueError(f"No existe configuración para entrega {numero}")
    
    return configs[numero]