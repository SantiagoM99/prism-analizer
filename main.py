"""
Script principal para análisis de proyectos LLM.

Este es el punto de entrada principal que orquesta todo el proceso:
1. Carga configuración
2. Ejecuta Fase 1 (extracción individual)
3. Ejecuta Fase 2 (consolidación y análisis)
4. Genera reportes finales
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

from config import get_config_for_entrega, EntregaConfig
from utils import (
    setup_logging,
    read_markdown_file,
    get_proyecto_files,
    create_results_summary
)
from extractor import ProyectoExtractor
from consolidator import ProyectoConsolidator


def initialize_gemini_api() -> bool:
    """
    Inicializa la API de Gemini con la API key.
    
    Returns:
        True si inicialización fue exitosa, False en caso contrario
    """
    # Cargar variables de entorno
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("ERROR: No se encontró GEMINI_API_KEY en las variables de entorno")
        print("Por favor crea un archivo .env con tu API key:")
        print("GEMINI_API_KEY=tu_api_key_aqui")
        return False
    
    try:
        genai.configure(api_key=api_key)
        print("API de Gemini configurada exitosamente")
        return True
    except Exception as e:
        print(f"ERROR configurando API de Gemini: {e}")
        return False


def run_analysis(config: EntregaConfig) -> bool:
    """
    Ejecuta el análisis completo de una entrega.
    
    Args:
        config: Configuración de la entrega a procesar
        
    Returns:
        True si el análisis fue exitoso, False en caso contrario
    """
    # Setup logging
    logger = setup_logging(config.output_dir / "logs")
    
    logger.info("\n" + "="*70)
    logger.info(f"ANÁLISIS DE PROYECTOS LLM - ENTREGA {config.numero_entrega}")
    logger.info("="*70 + "\n")
    
    logger.info(f"Configuración:")
    logger.info(f"  - Enunciado: {config.enunciado_path}")
    logger.info(f"  - Rúbrica: {config.rubrica_path}")
    logger.info(f"  - Proyectos: {config.proyectos_dir}")
    logger.info(f"  - Output: {config.output_dir}")
    logger.info(f"  - Modelo: {config.model_name}")
    logger.info(f"  - Temperatura: {config.temperature}\n")
    
    try:
        # 1. Cargar enunciado y rúbrica
        logger.info("Cargando enunciado y rúbrica...")
        enunciado = read_markdown_file(config.enunciado_path)
        rubrica = read_markdown_file(config.rubrica_path)
        logger.info("✓ Enunciado y rúbrica cargados\n")
        
        # 2. Obtener lista de proyectos
        proyecto_files = get_proyecto_files(config.proyectos_dir)
        
        if not proyecto_files:
            logger.error("No se encontraron archivos de proyecto para procesar")
            return False
        
        logger.info(f"Encontrados {len(proyecto_files)} proyectos para analizar\n")
        
        # 3. FASE 1: Extracción individual
        logger.info("="*70)
        logger.info("FASE 1: EXTRACCIÓN INDIVIDUAL DE PROYECTOS")
        logger.info("="*70 + "\n")
        
        extractor = ProyectoExtractor(
            model_name=config.model_name,
            temperature=config.temperature,
            max_retries=config.max_retries
        )
        
        extracciones, exitosos = extractor.extract_all_proyectos(
            proyecto_files=proyecto_files,
            enunciado=enunciado,
            rubrica=rubrica,
            output_dir=config.output_dir / "fase1_extracciones"
        )
        
        if exitosos == 0:
            logger.error("No se pudo procesar ningún proyecto exitosamente")
            return False
        
        # 4. FASE 2: Consolidación y análisis
        logger.info("\n" + "="*70)
        logger.info("FASE 2: CONSOLIDACIÓN Y ANÁLISIS AGREGADO")
        logger.info("="*70 + "\n")
        
        consolidator = ProyectoConsolidator(
            model_name=config.model_name,
            temperature=config.temperature + 0.1  # Un poco más alta para análisis
        )
        
        fase2_success = consolidator.run_full_consolidation(
            extracciones=extracciones,
            enunciado=enunciado,
            rubrica=rubrica,
            output_dir=config.output_dir / "fase2_consolidado"
        )
        
        # 5. Generar resumen de ejecución
        summary = create_results_summary(
            output_dir=config.output_dir,
            num_proyectos=len(proyecto_files),
            fase1_success=exitosos,
            fase2_success=fase2_success
        )
        
        # 6. Reporte final
        logger.info("\n" + "="*70)
        logger.info("ANÁLISIS COMPLETADO")
        logger.info("="*70)
        logger.info(f"\nResultados:")
        logger.info(f"  ✓ Proyectos procesados: {exitosos}/{len(proyecto_files)}")
        logger.info(f"  ✓ Tasa de éxito: {summary['fase1_tasa_exito']}")
        logger.info(f"  ✓ Consolidación: {'✓ Exitosa' if fase2_success else '✗ Fallida'}")
        logger.info(f"\nArchivos generados:")
        logger.info(f"  - Extracciones individuales: {config.output_dir / 'fase1_extracciones'}")
        logger.info(f"  - Análisis consolidado: {config.output_dir / 'fase2_consolidado'}")
        logger.info(f"  - Logs: {config.output_dir / 'logs'}")
        logger.info(f"\nArchivos principales:")
        logger.info(f"  CSV: {config.output_dir / 'fase2_consolidado' / 'decisiones_consolidadas.csv'}")
        logger.info(f"  Reporte: {config.output_dir / 'fase2_consolidado' / 'reporte_ejecutivo.md'}")
        logger.info(f"  JSON: {config.output_dir / 'fase2_consolidado' / 'analisis_consolidado.json'}")
        logger.info("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante el análisis: {e}", exc_info=True)
        return False


def main():
    """Función principal del script."""
    print("\n" + "="*70)
    print("ANALIZADOR DE PROYECTOS LLM")
    print("="*70 + "\n")
    
    # 1. Inicializar API de Gemini
    if not initialize_gemini_api():
        sys.exit(1)
    
    # 2. Obtener número de entrega (puede venir de argumento o input)
    if len(sys.argv) > 1:
        try:
            numero_entrega = int(sys.argv[1])
        except ValueError:
            print(f"ERROR: '{sys.argv[1]}' no es un número de entrega válido")
            sys.exit(1)
    else:
        # Pedir al usuario
        try:
            numero_entrega = int(input("Ingresa el número de entrega a procesar: "))
        except ValueError:
            print("ERROR: Debes ingresar un número válido")
            sys.exit(1)
    
    # 3. Cargar configuración
    try:
        config = get_config_for_entrega(numero_entrega)
    except ValueError as e:
        print(f"ERROR: {e}")
        print("\nAsegúrate de haber configurado la entrega en config.py")
        sys.exit(1)
    
    # 4. Ejecutar análisis
    success = run_analysis(config)
    
    # 5. Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()