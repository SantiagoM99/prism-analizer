"""
Utilidades generales para el proyecto.

Este módulo contiene funciones auxiliares para lectura de archivos,
parsing de JSON, logging, y otras operaciones comunes.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import re


def setup_logging(log_dir: Path, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configura el sistema de logging para el proyecto.
    
    Args:
        log_dir: Directorio donde guardar los logs
        log_level: Nivel de logging (default: INFO)
        
    Returns:
        Logger configurado
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"analisis_{timestamp}.log"
    
    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # También imprimir en consola
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging inicializado. Archivo: {log_file}")
    
    return logger


def read_markdown_file(file_path: Path) -> str:
    """
    Lee un archivo markdown y retorna su contenido.
    
    Args:
        file_path: Ruta al archivo markdown
        
    Returns:
        Contenido del archivo como string
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        UnicodeDecodeError: Si hay problemas de encoding
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    except UnicodeDecodeError:
        # Intentar con otro encoding común
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            logging.warning(f"Archivo {file_path} leído con encoding latin-1")
            return content
        except Exception as e:
            raise UnicodeDecodeError(f"Error leyendo {file_path}: {e}")


def extract_json_from_response(response_text: str) -> Optional[Dict[Any, Any]]:
    """
    Extrae JSON de la respuesta de Gemini, manejando casos donde
    el modelo incluye texto adicional antes/después del JSON.
    
    Args:
        response_text: Texto de respuesta del modelo
        
    Returns:
        Diccionario con el JSON parseado, o None si falla
    """
    # Intentar parsear directamente primero
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Buscar JSON dentro del texto usando regex
    # Busca el primer { hasta el último } balanceado
    json_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
    matches = re.finditer(json_pattern, response_text, re.DOTALL)
    
    for match in matches:
        try:
            potential_json = match.group(0)
            return json.loads(potential_json)
        except json.JSONDecodeError:
            continue
    
    # Si nada funciona, intentar buscar entre ```json y ```
    code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    code_matches = re.finditer(code_block_pattern, response_text, re.DOTALL)
    
    for match in code_matches:
        try:
            potential_json = match.group(1)
            return json.loads(potential_json)
        except json.JSONDecodeError:
            continue
    
    logging.error("No se pudo extraer JSON válido de la respuesta")
    logging.debug(f"Respuesta original: {response_text[:500]}...")
    return None


def save_json(data: Dict[Any, Any], file_path: Path, indent: int = 2) -> None:
    """
    Guarda un diccionario como archivo JSON.
    
    Args:
        data: Diccionario a guardar
        file_path: Ruta donde guardar el archivo
        indent: Espacios de indentación (default: 2)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    logging.info(f"JSON guardado en: {file_path}")


def load_json(file_path: Path) -> Dict[Any, Any]:
    """
    Carga un archivo JSON y retorna su contenido.
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Diccionario con el contenido del JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def get_proyecto_files(proyectos_dir: Path, extension: str = ".md") -> List[Path]:
    """
    Obtiene la lista de archivos de proyecto en un directorio.
    
    Args:
        proyectos_dir: Directorio conteniendo los proyectos
        extension: Extensión de archivos a buscar (default: .md)
        
    Returns:
        Lista ordenada de Paths a archivos de proyecto
    """
    files = sorted(proyectos_dir.glob(f"*{extension}"))
    
    if not files:
        logging.warning(f"No se encontraron archivos {extension} en {proyectos_dir}")
    else:
        logging.info(f"Encontrados {len(files)} archivos de proyecto")
    
    return files


def get_proyecto_identifier(file_path: Path) -> str:
    """
    Extrae un identificador único del nombre del archivo de proyecto.
    
    Args:
        file_path: Ruta al archivo de proyecto
        
    Returns:
        Identificador del proyecto (nombre del archivo sin extensión)
    """
    return file_path.stem


def save_markdown(content: str, file_path: Path) -> None:
    """
    Guarda contenido como archivo markdown.
    
    Args:
        content: Contenido markdown a guardar
        file_path: Ruta donde guardar el archivo
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logging.info(f"Markdown guardado en: {file_path}")


def create_results_summary(output_dir: Path, num_proyectos: int, 
                          fase1_success: int, fase2_success: bool) -> Dict[str, Any]:
    """
    Crea un resumen de los resultados del procesamiento.
    
    Args:
        output_dir: Directorio de resultados
        num_proyectos: Número total de proyectos procesados
        fase1_success: Número de proyectos procesados exitosamente en Fase 1
        fase2_success: Si Fase 2 fue exitosa
        
    Returns:
        Diccionario con el resumen
    """
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_proyectos": num_proyectos,
        "fase1_exitosos": fase1_success,
        "fase1_tasa_exito": f"{(fase1_success/num_proyectos)*100:.1f}%" if num_proyectos > 0 else "0%",
        "fase2_completada": fase2_success,
        "directorio_resultados": str(output_dir)
    }
    
    # Guardar resumen
    summary_path = output_dir / "resumen_ejecucion.json"
    save_json(summary, summary_path)
    
    return summary


def estimate_tokens(text: str) -> int:
    """
    Estima el número de tokens en un texto.
    
    Nota: Esta es una estimación aproximada. Para conteo exacto,
    usar la API de Gemini con count_tokens().
    
    Args:
        text: Texto a analizar
        
    Returns:
        Estimación aproximada de tokens
    """
    # Regla aproximada: 1 token ≈ 4 caracteres en español/inglés
    return len(text) // 4


def format_file_size(size_bytes: int) -> str:
    """
    Formatea el tamaño de archivo a formato legible.
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        String formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"