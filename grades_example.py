"""
Script de ejemplo para usar el módulo de calificaciones de forma independiente.

Este script demuestra cómo usar grades_reader y grades_analyzer sin ejecutar
el pipeline completo de análisis.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

from grades_reader import (
    GradesCSVReader,
    generate_grades_summary_markdown,
    load_grades_from_csv
)
from grades_analyzer import GradesAnalyzer
from utils import setup_logging, save_json, save_markdown


def ejemplo_lectura_basica():
    """
    Ejemplo 1: Lectura básica de un archivo CSV de calificaciones.
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Lectura Básica de CSV")
    print("="*70 + "\n")
    
    # Ruta al CSV (ajustar según tu estructura)
    csv_path = Path("./entregas/entrega1/calificaciones.csv")
    
    if not csv_path.exists():
        print(f"⚠ Archivo no encontrado: {csv_path}")
        print("Por favor ajusta la ruta en el script")
        return
    
    # Cargar calificaciones
    grades = load_grades_from_csv(csv_path)
    
    # Mostrar estadísticas
    stats = grades.get_estadisticas()
    print("📊 Estadísticas Generales:")
    print(f"  - Total grupos: {stats.get('total_grupos', 0)}")
    print(f"  - Grupos calificados: {stats.get('grupos_calificados', 0)}")
    print(f"  - Promedio: {stats.get('promedio', 0):.2f}")
    print(f"  - Nota máxima: {stats.get('nota_maxima', 0):.2f}")
    print(f"  - Nota mínima: {stats.get('nota_minima', 0):.2f}")
    print(f"  - Puntos totales posibles: {stats.get('puntos_totales_posibles', 0)}")
    
    # Mostrar criterios
    print(f"\n📋 Criterios de Evaluación ({len(grades.criterios)}):")
    for criterio in grades.criterios:
        print(f"  - {criterio.nombre}: {criterio.puntos_maximos} puntos")
    
    # Mostrar algunos grupos
    print(f"\n👥 Primeros 5 grupos:")
    for grupo in grades.grupos[:5]:
        porcentaje = (grupo.puntos_totales / grades.puntos_totales_posibles * 100) if grades.puntos_totales_posibles > 0 else 0
        print(f"  - {grupo.grupo_id}: {grupo.puntos_totales:.2f} puntos ({porcentaje:.1f}%)")


def ejemplo_comparacion_entregas():
    """
    Ejemplo 2: Comparar calificaciones entre dos entregas.
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Comparación entre Entregas")
    print("="*70 + "\n")
    
    # Rutas a los CSVs (ajustar según tu estructura)
    csv1_path = Path("./entregas/entrega1/calificaciones.csv")
    csv2_path = Path("./entregas/entrega2/calificaciones.csv")
    
    if not csv1_path.exists() or not csv2_path.exists():
        print(f"⚠ Uno o ambos archivos no encontrados")
        print(f"  Entrega 1: {csv1_path}")
        print(f"  Entrega 2: {csv2_path}")
        return
    
    # Cargar ambas entregas
    reader = GradesCSVReader()
    grades1 = reader.read_grades_csv(csv1_path)
    grades2 = reader.read_grades_csv(csv2_path)
    
    # Comparar
    comparacion = reader.compare_entregas(grades1, grades2)
    
    print(f"📈 Grupos comunes: {len(comparacion['grupos_comunes'])}")
    print(f"✅ Mejoras significativas: {len(comparacion['mejoras'])}")
    print(f"⚠ Retrocesos: {len(comparacion['retrocesos'])}")
    print(f"➡ Estables: {len(comparacion['estables'])}")
    
    # Mostrar mejores mejoras
    if comparacion['mejoras']:
        print(f"\n🏆 Top 3 Mejoras:")
        for mejora in comparacion['mejoras'][:3]:
            print(f"  {mejora['grupo_id']}: "
                  f"{mejora['entrega1_normalizado']:.1f}% → "
                  f"{mejora['entrega2_normalizado']:.1f}% "
                  f"(+{mejora['diferencia']:.1f}%)")


def ejemplo_generar_reporte():
    """
    Ejemplo 3: Generar reporte en Markdown de calificaciones.
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Generar Reporte Markdown")
    print("="*70 + "\n")
    
    csv_path = Path("./entregas/entrega1/calificaciones.csv")
    output_path = Path("./ejemplo_reporte_calificaciones.md")
    
    if not csv_path.exists():
        print(f"⚠ Archivo no encontrado: {csv_path}")
        return
    
    # Cargar y generar reporte
    grades = load_grades_from_csv(csv_path)
    reporte_md = generate_grades_summary_markdown(grades, entrega_numero=1)
    
    # Guardar
    save_markdown(reporte_md, output_path)
    
    print(f"✅ Reporte generado: {output_path}")
    print(f"📄 Longitud: {len(reporte_md)} caracteres")


def ejemplo_analisis_con_gemini():
    """
    Ejemplo 4: Análisis avanzado con Gemini (requiere extracciones previas).
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Análisis Avanzado con Gemini")
    print("="*70 + "\n")
    
    # Verificar API key
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠ GEMINI_API_KEY no encontrada en variables de entorno")
        print("Este ejemplo requiere configurar la API key")
        return
    
    genai.configure(api_key=api_key)
    
    # Rutas (ajustar según tu estructura)
    csv_path = Path("./entregas/entrega1/calificaciones.csv")
    extracciones_path = Path("./entregas/entrega1/resultados/fase1_extracciones")
    output_dir = Path("./ejemplo_analisis_grades")
    output_dir.mkdir(exist_ok=True)
    
    if not csv_path.exists():
        print(f"⚠ CSV no encontrado: {csv_path}")
        return
    
    if not extracciones_path.exists():
        print(f"⚠ Extracciones no encontradas: {extracciones_path}")
        print("Ejecuta primero el análisis completo (main.py) para generar extracciones")
        return
    
    # Cargar extracciones (simulado - en realidad cargarías los JSONs)
    print("ℹ Este ejemplo requiere extracciones previas del análisis completo")
    print("Para ejecutarlo:")
    print("1. Ejecuta main.py primero para generar extracciones")
    print("2. Luego usa grades_analyzer.run_full_grades_analysis()")


def main():
    """Ejecuta los ejemplos."""
    print("\n" + "="*70)
    print("EJEMPLOS DE USO DEL MÓDULO DE CALIFICACIONES")
    print("="*70)
    
    # Configurar logging básico
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar ejemplos
    try:
        ejemplo_lectura_basica()
    except Exception as e:
        print(f"Error en ejemplo 1: {e}")
    
    try:
        ejemplo_comparacion_entregas()
    except Exception as e:
        print(f"Error en ejemplo 2: {e}")
    
    try:
        ejemplo_generar_reporte()
    except Exception as e:
        print(f"Error en ejemplo 3: {e}")
    
    try:
        ejemplo_analisis_con_gemini()
    except Exception as e:
        print(f"Error en ejemplo 4: {e}")
    
    print("\n" + "="*70)
    print("FIN DE EJEMPLOS")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()