"""
Módulo de consolidación y análisis agregado (Fase 2).

Este módulo toma todas las extracciones de Fase 1 y genera
análisis consolidados, identificando patrones y insights generales.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from utils import (
    extract_json_from_response,
    save_json,
    save_markdown
)
from prompts import build_consolidation_prompt, build_summary_report_prompt


logger = logging.getLogger(__name__)


class ProyectoConsolidator:
    """
    Consolidador de análisis de múltiples proyectos.
    
    Esta clase maneja el análisis agregado de todos los proyectos,
    identificando patrones, tendencias y generando insights accionables.
    """
    
    def __init__(self, model_name: str, temperature: float = 0.2):
        """
        Inicializa el consolidador.
        
        Args:
            model_name: Nombre del modelo de Gemini a utilizar
            temperature: Temperatura para generación (un poco más alta que Fase 1)
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Configurar modelo con más tokens de output para análisis consolidado
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        
        logger.info(f"ProyectoConsolidator inicializado con modelo: {model_name}")
    
    def consolidate_analysis(self, extracciones: List[Dict[str, Any]], 
                           enunciado: str, rubrica: str) -> Optional[Dict[str, Any]]:
        """
        Genera análisis consolidado de todos los proyectos.
        
        Args:
            extracciones: Lista de diccionarios con extracciones de Fase 1
            enunciado: Contenido del enunciado de la actividad
            rubrica: Contenido de la rúbrica de evaluación
            
        Returns:
            Diccionario con el análisis consolidado, o None si falla
        """
        if not extracciones:
            logger.error("No hay extracciones para consolidar")
            return None
        
        logger.info(f"Iniciando consolidación de {len(extracciones)} proyectos...")
        
        try:
            # Construir prompt de consolidación
            prompt = build_consolidation_prompt(enunciado, rubrica, extracciones)
            
            logger.info("Enviando solicitud de consolidación a Gemini...")
            
            # Llamar a Gemini
            response = self.model.generate_content(prompt)
            
            # Extraer JSON de la respuesta
            consolidado = extract_json_from_response(response.text)
            
            if consolidado is None:
                logger.error("No se pudo extraer JSON del análisis consolidado")
                return None
            
            logger.info("✓ Consolidación exitosa")
            return consolidado
            
        except Exception as e:
            logger.error(f"Error durante consolidación: {e}")
            return None
    
    def generate_summary_report(self, consolidado: Dict[str, Any]) -> Optional[str]:
        """
        Genera un reporte ejecutivo en Markdown a partir del análisis consolidado.
        
        Args:
            consolidado: Diccionario con el análisis consolidado
            
        Returns:
            String con el reporte en formato Markdown, o None si falla
        """
        if not consolidado:
            logger.error("No hay datos consolidados para generar reporte")
            return None
        
        logger.info("Generando reporte ejecutivo en Markdown...")
        
        try:
            # Construir prompt para reporte
            prompt = build_summary_report_prompt(consolidado)
            
            # Llamar a Gemini
            response = self.model.generate_content(prompt)
            
            # El reporte ya viene en Markdown, no necesita parsing JSON
            reporte_md = response.text
            
            # Limpiar posibles code blocks si Gemini los agregó
            if reporte_md.startswith("```markdown"):
                reporte_md = reporte_md.replace("```markdown", "", 1)
            if reporte_md.startswith("```"):
                reporte_md = reporte_md.replace("```", "", 1)
            if reporte_md.endswith("```"):
                reporte_md = reporte_md.rsplit("```", 1)[0]
            
            reporte_md = reporte_md.strip()
            
            logger.info("✓ Reporte generado exitosamente")
            return reporte_md
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return None
    
    def generate_csv_table(self, extracciones: List[Dict[str, Any]], 
                          output_path: Path) -> bool:
        """
        Genera una tabla CSV consolidada con decisiones de todos los proyectos.
        
        Args:
            extracciones: Lista de extracciones de Fase 1
            output_path: Ruta donde guardar el CSV
            
        Returns:
            True si se generó exitosamente, False en caso contrario
        """
        try:
            import csv
            
            logger.info("Generando tabla CSV consolidada...")
            
            rows = []
            
            for extraccion in extracciones:
                proyecto_id = extraccion.get("_metadata", {}).get("proyecto_id", "unknown")
                metadata = extraccion.get("metadata", {})
                dominio = metadata.get("dominio", "N/A")
                
                # Extraer decisiones técnicas
                decisiones_tecnicas = extraccion.get("decisiones_tecnicas", {})
                for key, value in decisiones_tecnicas.items():
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    rows.append({
                        "Proyecto": proyecto_id,
                        "Dominio": dominio,
                        "Categoría": "Técnica",
                        "Tipo": key,
                        "Decisión": str(value)
                    })
                
                # Extraer decisiones de negocio
                decisiones_negocio = extraccion.get("decisiones_negocio", {})
                for key, value in decisiones_negocio.items():
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    rows.append({
                        "Proyecto": proyecto_id,
                        "Dominio": dominio,
                        "Categoría": "Negocio",
                        "Tipo": key,
                        "Decisión": str(value)
                    })
                
                # Extraer riesgos
                riesgos = extraccion.get("riesgos_identificados", [])
                for riesgo in riesgos:
                    rows.append({
                        "Proyecto": proyecto_id,
                        "Dominio": dominio,
                        "Categoría": "Riesgo",
                        "Tipo": riesgo.get("categoria", "N/A"),
                        "Decisión": f"{riesgo.get('riesgo', 'N/A')} | Mitigación: {riesgo.get('mitigacion', 'N/A')}"
                    })
            
            # Escribir CSV
            if rows:
                with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ["Proyecto", "Dominio", "Categoría", "Tipo", "Decisión"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                
                logger.info(f"✓ CSV generado: {output_path} ({len(rows)} filas)")
                return True
            else:
                logger.warning("No se generaron filas para el CSV")
                return False
                
        except Exception as e:
            logger.error(f"Error generando CSV: {e}")
            return False
    
    def run_full_consolidation(self, extracciones: List[Dict[str, Any]],
                              enunciado: str, rubrica: str,
                              output_dir: Path) -> bool:
        """
        Ejecuta el proceso completo de consolidación y genera todos los outputs.
        
        Args:
            extracciones: Lista de extracciones de Fase 1
            enunciado: Contenido del enunciado
            rubrica: Contenido de la rúbrica
            output_dir: Directorio donde guardar resultados
            
        Returns:
            True si todo fue exitoso, False en caso contrario
        """
        logger.info("\n" + "="*60)
        logger.info("INICIANDO FASE 2: CONSOLIDACIÓN Y ANÁLISIS")
        logger.info("="*60 + "\n")
        
        try:
            # 1. Análisis consolidado (JSON)
            consolidado = self.consolidate_analysis(extracciones, enunciado, rubrica)
            if not consolidado:
                logger.error("Falló la consolidación")
                return False
            
            consolidado_path = output_dir / "analisis_consolidado.json"
            save_json(consolidado, consolidado_path)
            
            # 2. Reporte ejecutivo (Markdown)
            reporte_md = self.generate_summary_report(consolidado)
            if reporte_md:
                reporte_path = output_dir / "reporte_ejecutivo.md"
                save_markdown(reporte_md, reporte_path)
            else:
                logger.warning("No se pudo generar reporte Markdown")
            
            # 3. Tabla CSV de decisiones
            csv_path = output_dir / "decisiones_consolidadas.csv"
            self.generate_csv_table(extracciones, csv_path)
            
            logger.info("\n" + "="*60)
            logger.info("✓ FASE 2 COMPLETADA EXITOSAMENTE")
            logger.info("="*60 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en proceso de consolidación: {e}")
            return False