"""
Módulo para lectura y procesamiento de archivos CSV de calificaciones.

Este módulo maneja la lectura de archivos CSV con estructura especial que contienen:
1. Metadatos de la rúbrica (puntos y descripciones) en las primeras filas
2. Datos de calificaciones de grupos en las filas siguientes
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class RubricCriterion:
    """
    Representa un criterio de la rúbrica de evaluación.
    
    Attributes:
        nombre: Nombre del criterio
        puntos_maximos: Puntos máximos asignables
        descripcion: Descripción detallada del criterio
        tiene_comentarios: Si el criterio tiene columna de comentarios
    """
    nombre: str
    puntos_maximos: float
    descripcion: str
    tiene_comentarios: bool = True


@dataclass
class GrupoCalificacion:
    """
    Representa la calificación de un grupo específico.
    
    Attributes:
        grupo_id: Identificador del grupo (ej: "Grupo01")
        repositorio: URL o nombre del repositorio
        tutor: Nombre del tutor responsable
        calificaciones: Diccionario con {criterio: puntos_obtenidos}
        comentarios: Diccionario con {criterio: comentario}
        puntos_totales: Total de puntos obtenidos
        retroalimentacion_general: Comentario general del evaluador
    """
    grupo_id: str
    repositorio: str = ""
    tutor: str = ""
    calificaciones: Dict[str, float] = field(default_factory=dict)
    comentarios: Dict[str, str] = field(default_factory=dict)
    puntos_totales: float = 0.0
    retroalimentacion_general: str = ""


@dataclass
class EntregaGrades:
    """
    Contiene toda la información de calificaciones de una entrega.
    
    Attributes:
        criterios: Lista de criterios de la rúbrica
        grupos: Lista de calificaciones por grupo
        puntos_totales_posibles: Suma de todos los puntos máximos
    """
    criterios: List[RubricCriterion] = field(default_factory=list)
    grupos: List[GrupoCalificacion] = field(default_factory=list)
    puntos_totales_posibles: float = 0.0
    
    def get_grupo(self, grupo_id: str) -> Optional[GrupoCalificacion]:
        """Busca un grupo por su ID."""
        for grupo in self.grupos:
            if grupo.grupo_id == grupo_id:
                return grupo
        return None
    
    def get_estadisticas(self) -> Dict[str, Any]:
        """Calcula estadísticas generales de las calificaciones."""
        if not self.grupos:
            return {}
        
        notas = [g.puntos_totales for g in self.grupos if g.puntos_totales > 0]
        
        if not notas:
            return {}
        
        return {
            "total_grupos": len(self.grupos),
            "grupos_calificados": len(notas),
            "promedio": sum(notas) / len(notas),
            "nota_maxima": max(notas),
            "nota_minima": min(notas),
            "puntos_totales_posibles": self.puntos_totales_posibles
        }


class GradesCSVReader:
    """
    Lector especializado para archivos CSV de calificaciones.
    
    Este lector maneja la estructura especial donde las primeras filas
    contienen metadatos de la rúbrica y las siguientes los datos de grupos.
    """
    
    # Constantes para identificar filas especiales
    FILA_PUNTOS_KEYWORD = "Puntos"
    FILA_DESCRIPCION_KEYWORD = "Descripción"
    COLUMNAS_FIJAS = ["Grupos", "Repositorio", "Tutor Responsable", "Criterio"]
    
    def __init__(self):
        """Inicializa el lector de CSVs."""
        pass
    
    def _parse_float_spanish(self, value: str) -> float:
        """
        Convierte un string con formato español (coma decimal) a float.
        
        Args:
            value: String con el número
            
        Returns:
            Valor float, o 0.0 si no se puede convertir
        """
        if not value or value.strip() == "":
            return 0.0
        
        try:
            # Reemplazar coma por punto
            value_clean = value.strip().replace(",", ".")
            return float(value_clean)
        except ValueError:
            logger.warning(f"No se pudo convertir '{value}' a float")
            return 0.0
    
    def _identificar_criterios(self, headers: List[str]) -> List[Tuple[str, int, bool]]:
        """
        Identifica los criterios de evaluación en los encabezados.
        
        Args:
            headers: Lista de encabezados del CSV
            
        Returns:
            Lista de tuplas (nombre_criterio, indice_columna, tiene_comentarios)
        """
        criterios = []
        i = len(self.COLUMNAS_FIJAS)  # Empezar después de las columnas fijas
        
        while i < len(headers):
            header = headers[i].strip()
            
            # Saltar columnas finales (Puntos totales, Retroalimentación)
            if header in ["Puntos totales", "Retroalimentación", ""]:
                break
            
            # Si el header termina en "Comentarios", es una columna de comentarios
            if header.endswith("Comentarios"):
                i += 1
                continue
            
            # Es un criterio nuevo
            nombre_criterio = header
            tiene_comentarios = False
            
            # Verificar si la siguiente columna son comentarios de este criterio
            if i + 1 < len(headers):
                siguiente = headers[i + 1].strip()
                if siguiente == f"{nombre_criterio} Comentarios":
                    tiene_comentarios = True
            
            criterios.append((nombre_criterio, i, tiene_comentarios))
            
            # Avanzar: +1 si no tiene comentarios, +2 si los tiene
            i += 2 if tiene_comentarios else 1
        
        return criterios
    
    def read_grades_csv(self, csv_path: Path) -> EntregaGrades:
        """
        Lee un archivo CSV de calificaciones y retorna objeto estructurado.
        
        Args:
            csv_path: Ruta al archivo CSV
            
        Returns:
            Objeto EntregaGrades con toda la información
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"Archivo CSV no encontrado: {csv_path}")
        
        logger.info(f"Leyendo archivo de calificaciones: {csv_path}")
        
        entrega_grades = EntregaGrades()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) < 4:
            logger.error("El CSV no tiene suficientes filas")
            return entrega_grades
        
        # Fila 0: Headers
        headers = rows[0]
        
        # Identificar criterios
        criterios_info = self._identificar_criterios(headers)
        logger.info(f"Criterios identificados: {len(criterios_info)}")
        
        # Fila 1: Puntos (buscar fila que contenga "Puntos")
        fila_puntos = None
        fila_descripcion = None
        fila_inicio_grupos = None
        
        for idx, row in enumerate(rows[1:], start=1):
            if len(row) > 3 and row[3] == self.FILA_PUNTOS_KEYWORD:
                fila_puntos = row
            elif len(row) > 3 and row[3] == self.FILA_DESCRIPCION_KEYWORD:
                fila_descripcion = row
            elif len(row) > 0 and row[0].startswith("Grupo"):
                fila_inicio_grupos = idx
                break
        
        # Parsear criterios de la rúbrica
        if fila_puntos and fila_descripcion:
            for nombre_criterio, col_idx, tiene_comentarios in criterios_info:
                puntos = self._parse_float_spanish(fila_puntos[col_idx])
                descripcion = fila_descripcion[col_idx] if col_idx < len(fila_descripcion) else ""
                
                criterio = RubricCriterion(
                    nombre=nombre_criterio,
                    puntos_maximos=puntos,
                    descripcion=descripcion,
                    tiene_comentarios=tiene_comentarios
                )
                entrega_grades.criterios.append(criterio)
                entrega_grades.puntos_totales_posibles += puntos
            
            logger.info(f"Rúbrica parseada: {len(entrega_grades.criterios)} criterios, "
                       f"{entrega_grades.puntos_totales_posibles} puntos totales")
        
        # Parsear grupos
        if fila_inicio_grupos:
            for row in rows[fila_inicio_grupos:]:
                if len(row) < 4 or not row[0].startswith("Grupo"):
                    continue
                
                grupo = GrupoCalificacion(
                    grupo_id=row[0].strip(),
                    repositorio=row[1].strip() if len(row) > 1 else "",
                    tutor=row[2].strip() if len(row) > 2 else ""
                )
                
                # Parsear calificaciones y comentarios por criterio
                for nombre_criterio, col_idx, tiene_comentarios in criterios_info:
                    # Calificación
                    if col_idx < len(row):
                        puntos = self._parse_float_spanish(row[col_idx])
                        grupo.calificaciones[nombre_criterio] = puntos
                    
                    # Comentario (si existe)
                    if tiene_comentarios and (col_idx + 1) < len(row):
                        comentario = row[col_idx + 1].strip()
                        if comentario:
                            grupo.comentarios[nombre_criterio] = comentario
                
                # Puntos totales (penúltima columna típicamente)
                if len(row) >= len(headers) - 1:
                    grupo.puntos_totales = self._parse_float_spanish(row[len(headers) - 2])
                
                # Retroalimentación general (última columna)
                if len(row) >= len(headers):
                    grupo.retroalimentacion_general = row[len(headers) - 1].strip()
                
                entrega_grades.grupos.append(grupo)
            
            logger.info(f"Grupos parseados: {len(entrega_grades.grupos)}")
        
        return entrega_grades
    
    def compare_entregas(self, entrega1: EntregaGrades, 
                        entrega2: EntregaGrades) -> Dict[str, Any]:
        """
        Compara las calificaciones de dos entregas.
        
        Args:
            entrega1: Primera entrega
            entrega2: Segunda entrega
            
        Returns:
            Diccionario con análisis comparativo
        """
        comparacion = {
            "grupos_comunes": [],
            "mejoras": [],
            "retrocesos": [],
            "estables": []
        }
        
        # Encontrar grupos comunes
        grupos1_ids = {g.grupo_id for g in entrega1.grupos}
        grupos2_ids = {g.grupo_id for g in entrega2.grupos}
        grupos_comunes = grupos1_ids & grupos2_ids
        
        comparacion["grupos_comunes"] = sorted(list(grupos_comunes))
        
        for grupo_id in grupos_comunes:
            g1 = entrega1.get_grupo(grupo_id)
            g2 = entrega2.get_grupo(grupo_id)
            
            if g1 and g2:
                # Normalizar por puntos totales posibles
                nota1_normalizada = (g1.puntos_totales / entrega1.puntos_totales_posibles) * 100 if entrega1.puntos_totales_posibles > 0 else 0
                nota2_normalizada = (g2.puntos_totales / entrega2.puntos_totales_posibles) * 100 if entrega2.puntos_totales_posibles > 0 else 0
                
                diferencia = nota2_normalizada - nota1_normalizada
                
                resultado = {
                    "grupo_id": grupo_id,
                    "entrega1_puntos": g1.puntos_totales,
                    "entrega2_puntos": g2.puntos_totales,
                    "entrega1_normalizado": round(nota1_normalizada, 2),
                    "entrega2_normalizado": round(nota2_normalizada, 2),
                    "diferencia": round(diferencia, 2)
                }
                
                if diferencia > 5:  # Mejora significativa (>5%)
                    comparacion["mejoras"].append(resultado)
                elif diferencia < -5:  # Retroceso significativo
                    comparacion["retrocesos"].append(resultado)
                else:
                    comparacion["estables"].append(resultado)
        
        # Ordenar por diferencia
        comparacion["mejoras"].sort(key=lambda x: x["diferencia"], reverse=True)
        comparacion["retrocesos"].sort(key=lambda x: x["diferencia"])
        
        return comparacion


def generate_grades_summary_markdown(entrega_grades: EntregaGrades, 
                                     entrega_numero: int) -> str:
    """
    Genera un reporte en Markdown con resumen de calificaciones.
    
    Args:
        entrega_grades: Objeto con las calificaciones
        entrega_numero: Número de la entrega
        
    Returns:
        String con el reporte en formato Markdown
    """
    md = f"# Resumen de Calificaciones - Entrega {entrega_numero}\n\n"
    
    # Estadísticas generales
    stats = entrega_grades.get_estadisticas()
    if stats:
        md += "## Estadísticas Generales\n\n"
        md += f"- **Total de grupos**: {stats['total_grupos']}\n"
        md += f"- **Grupos calificados**: {stats['grupos_calificados']}\n"
        md += f"- **Promedio**: {stats['promedio']:.2f} / {stats['puntos_totales_posibles']}\n"
        md += f"- **Nota máxima**: {stats['nota_maxima']:.2f}\n"
        md += f"- **Nota mínima**: {stats['nota_minima']:.2f}\n\n"
    
    # Criterios de la rúbrica
    md += "## Criterios de Evaluación\n\n"
    md += "| Criterio | Puntos Máximos |\n"
    md += "|----------|----------------|\n"
    for criterio in entrega_grades.criterios:
        md += f"| {criterio.nombre} | {criterio.puntos_maximos} |\n"
    md += f"| **TOTAL** | **{entrega_grades.puntos_totales_posibles}** |\n\n"
    
    # Distribución de notas
    md += "## Distribución de Notas\n\n"
    md += "| Grupo | Tutor | Puntos Totales |\n"
    md += "|-------|-------|----------------|\n"
    
    grupos_ordenados = sorted(entrega_grades.grupos, 
                             key=lambda g: g.puntos_totales, 
                             reverse=True)
    
    for grupo in grupos_ordenados:
        if grupo.puntos_totales > 0:
            porcentaje = (grupo.puntos_totales / entrega_grades.puntos_totales_posibles) * 100
            md += f"| {grupo.grupo_id} | {grupo.tutor} | {grupo.puntos_totales:.2f} ({porcentaje:.1f}%) |\n"
    
    md += "\n"
    
    # Análisis por criterio
    md += "## Desempeño por Criterio\n\n"
    for criterio in entrega_grades.criterios:
        puntos_obtenidos = []
        for grupo in entrega_grades.grupos:
            if criterio.nombre in grupo.calificaciones:
                puntos = grupo.calificaciones[criterio.nombre]
                if puntos > 0:
                    puntos_obtenidos.append(puntos)
        
        if puntos_obtenidos:
            promedio = sum(puntos_obtenidos) / len(puntos_obtenidos)
            porcentaje_logro = (promedio / criterio.puntos_maximos) * 100
            
            md += f"### {criterio.nombre}\n\n"
            md += f"- Promedio: {promedio:.2f} / {criterio.puntos_maximos} ({porcentaje_logro:.1f}%)\n"
            md += f"- Grupos evaluados: {len(puntos_obtenidos)}\n\n"
    
    return md


# Función auxiliar para uso rápido
def load_grades_from_csv(csv_path: Path) -> EntregaGrades:
    """
    Función helper para cargar rápidamente calificaciones desde CSV.
    
    Args:
        csv_path: Ruta al archivo CSV
        
    Returns:
        Objeto EntregaGrades con la información
    """
    reader = GradesCSVReader()
    return reader.read_grades_csv(csv_path)