"""
Módulo de análisis de calificaciones.

Este módulo integra las calificaciones CSV con las extracciones y consolidaciones
del análisis de proyectos, permitiendo análisis comparativos y enriquecidos.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import google.generativeai as genai

from grades_reader import (
    GradesCSVReader, 
    EntregaGrades, 
    generate_grades_summary_markdown
)
from utils import save_json, save_markdown
from prompts import build_grades_analysis_prompt


logger = logging.getLogger(__name__)


class GradesAnalyzer:
    """
    Analizador que combina calificaciones con extracciones de proyectos.
    
    Esta clase permite generar insights que combinan las evaluaciones
    formales (calificaciones) con el análisis automatizado de proyectos.
    """
    
    def __init__(self, model_name: str, temperature: float = 0.2):
        """
        Inicializa el analizador de calificaciones.
        
        Args:
            model_name: Nombre del modelo de Gemini a utilizar
            temperature: Temperatura para generación
        """
        self.model_name = model_name
        self.temperature = temperature
        self.reader = GradesCSVReader()
        
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
        
        logger.info(f"GradesAnalyzer inicializado con modelo: {model_name}")
    
    def load_grades(self, csv_path: Path) -> Optional[EntregaGrades]:
        """
        Carga las calificaciones desde un archivo CSV.
        
        Args:
            csv_path: Ruta al archivo CSV
            
        Returns:
            Objeto EntregaGrades con las calificaciones, o None si falla
        """
        try:
            grades = self.reader.read_grades_csv(csv_path)
            logger.info(f"Calificaciones cargadas: {len(grades.grupos)} grupos, "
                       f"{len(grades.criterios)} criterios")
            return grades
        except Exception as e:
            logger.error(f"Error cargando calificaciones: {e}")
            return None
    
    def enrich_extractions_with_grades(self, 
                                      extracciones: List[Dict[str, Any]],
                                      grades: EntregaGrades) -> List[Dict[str, Any]]:
        """
        Enriquece las extracciones con información de calificaciones.
        
        Args:
            extracciones: Lista de extracciones de proyectos
            grades: Calificaciones de la entrega
            
        Returns:
            Lista de extracciones enriquecidas con calificaciones
        """
        extracciones_enriquecidas = []
        
        for extraccion in extracciones:
            proyecto_id = extraccion.get("_metadata", {}).get("proyecto_id", "")
            
            # Intentar encontrar el grupo correspondiente
            # Asumimos que el proyecto_id tiene formato similar al grupo_id
            grupo_calificacion = None
            
            # Intentar match exacto primero
            for grupo in grades.grupos:
                if grupo.grupo_id.lower() in proyecto_id.lower():
                    grupo_calificacion = grupo
                    break
            
            # Si no hay match, intentar extraer número de grupo
            if not grupo_calificacion:
                import re
                match = re.search(r'grupo[\s_-]?(\d+)', proyecto_id, re.IGNORECASE)
                if match:
                    numero_grupo = match.group(1)
                    grupo_id_buscar = f"Grupo{numero_grupo.zfill(2)}"
                    grupo_calificacion = grades.get_grupo(grupo_id_buscar)
            
            # Enriquecer extracción con calificaciones
            extraccion_enriquecida = extraccion.copy()
            
            if grupo_calificacion:
                extraccion_enriquecida["calificacion"] = {
                    "grupo_id": grupo_calificacion.grupo_id,
                    "tutor": grupo_calificacion.tutor,
                    "puntos_totales": grupo_calificacion.puntos_totales,
                    "puntos_posibles": grades.puntos_totales_posibles,
                    "porcentaje": (grupo_calificacion.puntos_totales / grades.puntos_totales_posibles * 100) 
                                 if grades.puntos_totales_posibles > 0 else 0,
                    "calificaciones_por_criterio": grupo_calificacion.calificaciones,
                    "comentarios": grupo_calificacion.comentarios,
                    "retroalimentacion_general": grupo_calificacion.retroalimentacion_general
                }
                logger.debug(f"Calificación añadida a {proyecto_id}: "
                           f"{grupo_calificacion.puntos_totales}/{grades.puntos_totales_posibles}")
            else:
                extraccion_enriquecida["calificacion"] = None
                logger.warning(f"No se encontró calificación para {proyecto_id}")
            
            extracciones_enriquecidas.append(extraccion_enriquecida)
        
        grupos_con_calificacion = sum(1 for e in extracciones_enriquecidas 
                                     if e.get("calificacion") is not None)
        logger.info(f"Extracciones enriquecidas: {grupos_con_calificacion}/{len(extracciones)} "
                   f"con calificaciones asociadas")
        
        return extracciones_enriquecidas
    
    def analyze_grades_vs_extraction(self,
                                    extracciones_enriquecidas: List[Dict[str, Any]],
                                    grades: EntregaGrades) -> Dict[str, Any]:
        """
        Analiza la correlación entre calificaciones y análisis automatizado.
        
        Args:
            extracciones_enriquecidas: Extracciones con calificaciones
            grades: Calificaciones de la entrega
            
        Returns:
            Diccionario con análisis comparativo
        """
        analisis = {
            "resumen": {},
            "correlaciones": [],
            "discrepancias": [],
            "insights": []
        }
        
        proyectos_con_calificacion = [e for e in extracciones_enriquecidas 
                                     if e.get("calificacion") is not None]
        
        if not proyectos_con_calificacion:
            logger.warning("No hay proyectos con calificaciones para analizar")
            return analisis
        
        # Análisis de correlación entre fortalezas/debilidades y calificaciones
        for extraccion in proyectos_con_calificacion:
            calificacion = extraccion["calificacion"]
            proyecto_id = extraccion.get("_metadata", {}).get("proyecto_id", "unknown")
            
            num_fortalezas = len(extraccion.get("fortalezas_generales", []))
            num_debilidades = len(extraccion.get("debilidades_generales", []))
            porcentaje_nota = calificacion["porcentaje"]
            
            correlacion = {
                "proyecto_id": proyecto_id,
                "grupo_id": calificacion["grupo_id"],
                "nota_porcentaje": round(porcentaje_nota, 2),
                "num_fortalezas": num_fortalezas,
                "num_debilidades": num_debilidades,
                "balance": num_fortalezas - num_debilidades
            }
            
            # Detectar discrepancias (nota alta con muchas debilidades o viceversa)
            if porcentaje_nota > 80 and num_debilidades > num_fortalezas:
                analisis["discrepancias"].append({
                    **correlacion,
                    "tipo": "nota_alta_muchas_debilidades",
                    "descripcion": f"Nota alta ({porcentaje_nota:.1f}%) pero más debilidades ({num_debilidades}) que fortalezas ({num_fortalezas})"
                })
            elif porcentaje_nota < 60 and num_fortalezas > num_debilidades:
                analisis["discrepancias"].append({
                    **correlacion,
                    "tipo": "nota_baja_muchas_fortalezas",
                    "descripcion": f"Nota baja ({porcentaje_nota:.1f}%) pero más fortalezas ({num_fortalezas}) que debilidades ({num_debilidades})"
                })
            
            analisis["correlaciones"].append(correlacion)
        
        # Calcular estadísticas
        notas = [c["nota_porcentaje"] for c in analisis["correlaciones"]]
        balances = [c["balance"] for c in analisis["correlaciones"]]
        
        analisis["resumen"] = {
            "total_proyectos_analizados": len(proyectos_con_calificacion),
            "nota_promedio": sum(notas) / len(notas) if notas else 0,
            "balance_promedio": sum(balances) / len(balances) if balances else 0,
            "proyectos_con_discrepancias": len(analisis["discrepancias"])
        }
        
        return analisis
    
    def generate_comparative_report(self,
                                   extracciones_enriquecidas: List[Dict[str, Any]],
                                   grades: EntregaGrades,
                                   analisis_comparativo: Dict[str, Any]) -> Optional[str]:
        """
        Genera un reporte comparativo usando Gemini.
        
        Args:
            extracciones_enriquecidas: Extracciones con calificaciones
            grades: Calificaciones de la entrega
            analisis_comparativo: Análisis de correlaciones
            
        Returns:
            Reporte en formato Markdown, o None si falla
        """
        try:
            logger.info("Generando reporte comparativo con Gemini...")
            
            # Preparar datos para el prompt
            datos_prompt = {
                "estadisticas_grades": grades.get_estadisticas(),
                "analisis_comparativo": analisis_comparativo,
                "ejemplos_proyectos": []
            }
            
            # Incluir algunos ejemplos de proyectos (los 3 con mejor y peor nota)
            proyectos_con_nota = [e for e in extracciones_enriquecidas 
                                 if e.get("calificacion") is not None]
            proyectos_ordenados = sorted(proyectos_con_nota, 
                                        key=lambda x: x["calificacion"]["puntos_totales"],
                                        reverse=True)
            
            # Top 3 y bottom 3
            for proyecto in proyectos_ordenados[:3] + proyectos_ordenados[-3:]:
                ejemplo = {
                    "proyecto_id": proyecto.get("_metadata", {}).get("proyecto_id"),
                    "grupo_id": proyecto["calificacion"]["grupo_id"],
                    "nota": proyecto["calificacion"]["puntos_totales"],
                    "porcentaje": proyecto["calificacion"]["porcentaje"],
                    "fortalezas": proyecto.get("fortalezas_generales", [])[:3],
                    "debilidades": proyecto.get("debilidades_generales", [])[:3],
                    "comentarios_tutor": list(proyecto["calificacion"]["comentarios"].values())[:2]
                }
                datos_prompt["ejemplos_proyectos"].append(ejemplo)
            
            # Construir y ejecutar prompt
            prompt = build_grades_analysis_prompt(datos_prompt)
            response = self.model.generate_content(prompt)
            
            # Limpiar respuesta
            reporte = response.text.strip()
            if reporte.startswith("```markdown"):
                reporte = reporte.replace("```markdown", "", 1)
            if reporte.startswith("```"):
                reporte = reporte.replace("```", "", 1)
            if reporte.endswith("```"):
                reporte = reporte.rsplit("```", 1)[0]
            
            logger.info("✓ Reporte comparativo generado")
            return reporte.strip()
            
        except Exception as e:
            logger.error(f"Error generando reporte comparativo: {e}")
            return None
    
    def run_full_grades_analysis(self,
                                csv_path: Path,
                                extracciones: List[Dict[str, Any]],
                                output_dir: Path) -> bool:
        """
        Ejecuta el análisis completo de calificaciones.
        
        Args:
            csv_path: Ruta al CSV de calificaciones
            extracciones: Lista de extracciones de proyectos
            output_dir: Directorio donde guardar resultados
            
        Returns:
            True si fue exitoso, False en caso contrario
        """
        logger.info("\n" + "="*60)
        logger.info("INICIANDO FASE 3: ANÁLISIS DE CALIFICACIONES")
        logger.info("="*60 + "\n")
        
        try:
            # 1. Cargar calificaciones
            grades = self.load_grades(csv_path)
            if not grades:
                logger.error("No se pudieron cargar las calificaciones")
                return False
            
            # 2. Generar resumen básico de calificaciones
            resumen_md = generate_grades_summary_markdown(grades, 
                                                         entrega_numero=2)
            save_markdown(resumen_md, output_dir / "resumen_calificaciones.md")
            
            # 3. Enriquecer extracciones con calificaciones
            extracciones_enriquecidas = self.enrich_extractions_with_grades(
                extracciones, grades
            )
            
            # Guardar extracciones enriquecidas
            save_json(extracciones_enriquecidas, 
                     output_dir / "extracciones_enriquecidas.json")
            
            # 4. Análisis comparativo
            analisis_comparativo = self.analyze_grades_vs_extraction(
                extracciones_enriquecidas, grades
            )
            save_json(analisis_comparativo, 
                     output_dir / "analisis_comparativo.json")
            
            # 5. Reporte comparativo con Gemini
            reporte_comparativo = self.generate_comparative_report(
                extracciones_enriquecidas, grades, analisis_comparativo
            )
            if reporte_comparativo:
                save_markdown(reporte_comparativo,
                            output_dir / "reporte_comparativo.md")
            
            logger.info("\n" + "="*60)
            logger.info("✓ FASE 3 COMPLETADA EXITOSAMENTE")
            logger.info("="*60 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en análisis de calificaciones: {e}")
            return False