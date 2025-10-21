"""
Módulo de extracción individual de proyectos (Fase 1).

Este módulo maneja el procesamiento individual de cada proyecto,
extrayendo información estructurada usando Gemini.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import google.generativeai as genai

from utils import (
    read_markdown_file, 
    extract_json_from_response,
    save_json,
    get_proyecto_identifier,
    estimate_tokens
)
from prompts import build_extraction_prompt


logger = logging.getLogger(__name__)


class ProyectoExtractor:
    """
    Extractor de información estructurada de proyectos individuales.
    
    Esta clase maneja la comunicación con Gemini para extraer y estructurar
    información de cada proyecto según el enunciado y rúbrica.
    """
    
    def __init__(self, model_name: str, temperature: float = 0.1, 
                 max_retries: int = 3):
        """
        Inicializa el extractor.
        
        Args:
            model_name: Nombre del modelo de Gemini a utilizar
            temperature: Temperatura para generación (0.0 - 1.0)
            max_retries: Número máximo de reintentos en caso de error
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Configurar modelo
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        
        logger.info(f"ProyectoExtractor inicializado con modelo: {model_name}")
    
    def extract_proyecto(self, proyecto_path: Path, enunciado: str, 
                        rubrica: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información estructurada de un proyecto individual.
        
        Args:
            proyecto_path: Ruta al archivo markdown del proyecto
            enunciado: Contenido del enunciado de la actividad
            rubrica: Contenido de la rúbrica de evaluación
            
        Returns:
            Diccionario con la información extraída, o None si falla
        """
        proyecto_id = get_proyecto_identifier(proyecto_path)
        logger.info(f"Procesando proyecto: {proyecto_id}")
        
        try:
            # Leer contenido del proyecto
            proyecto_content = read_markdown_file(proyecto_path)
            logger.debug(f"Proyecto leído: {len(proyecto_content)} caracteres, "
                        f"~{estimate_tokens(proyecto_content)} tokens estimados")
            
            # Construir prompt
            prompt = build_extraction_prompt(enunciado, rubrica, proyecto_content)
            
            # Intentar extracción con reintentos
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"Intento {attempt}/{self.max_retries} para {proyecto_id}")
                    
                    # Llamar a Gemini
                    response = self.model.generate_content(prompt)
                    
                    # Extraer JSON de la respuesta
                    extracted_data = extract_json_from_response(response.text)
                    
                    if extracted_data is None:
                        logger.warning(f"No se pudo extraer JSON en intento {attempt}")
                        if attempt < self.max_retries:
                            time.sleep(2 ** attempt)  # Backoff exponencial
                            continue
                        else:
                            logger.error(f"Falló extracción de {proyecto_id} después de {self.max_retries} intentos")
                            return None
                    
                    # Agregar metadata adicional
                    extracted_data["_metadata"] = {
                        "proyecto_id": proyecto_id,
                        "archivo_fuente": str(proyecto_path),
                        "modelo_usado": self.model_name,
                        "tokens_estimados": estimate_tokens(proyecto_content)
                    }
                    
                    logger.info(f"✓ Extracción exitosa para {proyecto_id}")
                    return extracted_data
                    
                except Exception as e:
                    logger.error(f"Error en intento {attempt} para {proyecto_id}: {e}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        logger.error(f"Falló procesamiento de {proyecto_id} después de {self.max_retries} intentos")
                        return None
            
        except Exception as e:
            logger.error(f"Error leyendo proyecto {proyecto_id}: {e}")
            return None
    
    def extract_all_proyectos(self, proyecto_files: list[Path], enunciado: str,
                             rubrica: str, output_dir: Path) -> tuple[list[Dict[str, Any]], int]:
        """
        Extrae información de todos los proyectos en una lista.
        
        Args:
            proyecto_files: Lista de rutas a archivos de proyecto
            enunciado: Contenido del enunciado
            rubrica: Contenido de la rúbrica
            output_dir: Directorio donde guardar extracciones individuales
            
        Returns:
            Tupla con (lista de extracciones exitosas, número de proyectos exitosos)
        """
        extracciones = []
        exitosos = 0
        total = len(proyecto_files)
        
        logger.info(f"Iniciando extracción de {total} proyectos...")
        
        for idx, proyecto_path in enumerate(proyecto_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Progreso: {idx}/{total} ({(idx/total)*100:.1f}%)")
            logger.info(f"{'='*60}")
            
            # Extraer proyecto
            resultado = self.extract_proyecto(proyecto_path, enunciado, rubrica)
            
            if resultado:
                extracciones.append(resultado)
                exitosos += 1
                
                # Guardar extracción individual
                proyecto_id = get_proyecto_identifier(proyecto_path)
                output_file = output_dir / f"{proyecto_id}_extraction.json"
                save_json(resultado, output_file)
                
            else:
                logger.warning(f"✗ Falló extracción de {proyecto_path.name}")
            
            # Pausa breve entre proyectos para evitar rate limits
            if idx < total:
                time.sleep(1)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Fase 1 completada: {exitosos}/{total} proyectos procesados exitosamente")
        logger.info(f"Tasa de éxito: {(exitosos/total)*100:.1f}%")
        logger.info(f"{'='*60}\n")
        
        return extracciones, exitosos