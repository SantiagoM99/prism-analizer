"""
Templates de prompts para Gemini.

Este módulo contiene las funciones que construyen los prompts para
las diferentes fases del análisis.
"""

from typing import Dict, List


def build_extraction_prompt(enunciado: str, rubrica: str, proyecto_content: str) -> str:
    """
    Construye el prompt para la Fase 1: Extracción individual de proyectos.
    
    Este prompt instruye a Gemini para analizar un proyecto específico
    y extraer información estructurada basándose en el enunciado y la rúbrica.
    
    Args:
        enunciado: Contenido completo del enunciado de la actividad
        rubrica: Contenido completo de la rúbrica de evaluación
        proyecto_content: Contenido del markdown del proyecto a analizar
        
    Returns:
        Prompt completo listo para enviar a Gemini
    """
    return f"""Eres un asistente experto en analizar proyectos de aplicaciones LLM (Large Language Models).

# CONTEXTO DE LA ACTIVIDAD

## Enunciado de la Actividad
{enunciado}

## Rúbrica de Evaluación
{rubrica}

# TU TAREA

Analiza el siguiente proyecto estudiantil y extrae información estructurada en formato JSON.

## Proyecto a Analizar
{proyecto_content}

# INSTRUCCIONES DE EXTRACCIÓN

Debes generar un JSON con la siguiente estructura:

{{
  "metadata": {{
    "nombre_proyecto": "string - Título o nombre del proyecto identificado",
    "dominio": "string - Área de aplicación (jurídico, corporativo, salud, educación, etc.)",
    "problema_identificado": "string - Resumen conciso del problema que buscan resolver"
  }},
  
  "cumplimiento_enunciado": [
    {{
      "seccion_enunciado": "string - Qué pedía el enunciado",
      "como_lo_abordaron": "string - Cómo el equipo respondió a este punto",
      "decisiones_clave": ["lista de decisiones específicas tomadas"],
      "calidad": "string - alta/media/baja según completitud de la respuesta"
    }}
  ],
  
  "evaluacion_rubrica": [
    {{
      "criterio": "string - Criterio de la rúbrica",
      "evidencia_encontrada": "string - Qué evidencia hay en el documento",
      "fortalezas": ["lista de aspectos bien ejecutados"],
      "debilidades": ["lista de aspectos débiles o faltantes"],
      "cumplimiento_estimado": "string - excelente/bueno/regular/insuficiente"
    }}
  ],
  
  "decisiones_tecnicas": {{
    "arquitectura": "string - Arquitectura propuesta (RAG, fine-tuning, etc.)",
    "modelos_llm": ["lista de modelos mencionados"],
    "tecnologias": ["lista de tecnologías y herramientas"],
    "integraciones": ["lista de sistemas externos o fuentes de datos"]
  }},
  
  "decisiones_negocio": {{
    "usuarios_objetivo": ["lista de perfiles de usuario identificados"],
    "metricas_exito": ["lista de métricas propuestas"],
    "alcance_mvp": "string - Descripción del alcance inicial",
    "escalabilidad": "string - Consideraciones de escalabilidad mencionadas"
  }},
  
  "riesgos_identificados": [
    {{
      "riesgo": "string - Descripción del riesgo",
      "mitigacion": "string - Estrategia de mitigación propuesta",
      "categoria": "string - técnico/negocio/ético/regulatorio"
    }}
  ],
  
  "fortalezas_generales": ["lista de fortalezas destacables del proyecto"],
  "debilidades_generales": ["lista de debilidades o gaps identificados"],
  
  "observaciones": "string - Cualquier observación adicional relevante"
}}

# IMPORTANTE

1. Si alguna información no está presente en el documento, usa null o arrays vacíos
2. Sé preciso y objetivo en tu análisis
3. Extrae decisiones explícitas del documento, no inventes información
4. Para la evaluación según rúbrica, justifica tu evaluación con evidencia específica
5. El output debe ser ÚNICAMENTE el JSON, sin texto adicional antes o después

Genera el JSON ahora:"""


def build_consolidation_prompt(enunciado: str, rubrica: str, 
                               extracciones: List[Dict]) -> str:
    """
    Construye el prompt para la Fase 2: Análisis consolidado.
    
    Este prompt instruye a Gemini para analizar todos los proyectos
    en conjunto e identificar patrones, tendencias y insights generales.
    
    Args:
        enunciado: Contenido completo del enunciado de la actividad
        rubrica: Contenido completo de la rúbrica de evaluación
        extracciones: Lista de diccionarios con las extracciones de Fase 1
        
    Returns:
        Prompt completo listo para enviar a Gemini
    """
    import json
    extracciones_json = json.dumps(extracciones, indent=2, ensure_ascii=False)
    
    return f"""Eres un asistente experto en analizar proyectos de aplicaciones LLM a nivel agregado.

# CONTEXTO

## Enunciado de la Actividad
{enunciado}

## Rúbrica de Evaluación
{rubrica}

## Datos de {len(extracciones)} Proyectos Analizados
{extracciones_json}

# TU TAREA

Realiza un análisis consolidado de todos los proyectos y genera insights accionables.

# ESTRUCTURA DEL ANÁLISIS

Genera un JSON con la siguiente estructura:

{{
  "resumen_ejecutivo": {{
    "total_proyectos": {len(extracciones)},
    "dominios_identificados": {{"dominio": "cantidad"}},
    "patron_general": "string - Descripción de patrones observados a alto nivel"
  }},
  
  "decisiones_comunes": [
    {{
      "decision": "string - Decisión común entre proyectos",
      "frecuencia": "number - Cantidad de proyectos que la tomaron",
      "porcentaje": "number - Porcentaje del total",
      "categoria": "string - técnica/negocio/diseño/riesgos",
      "ejemplos": ["lista de 2-3 ejemplos específicos de proyectos"]
    }}
  ],
  
  "tecnologias_mas_usadas": [
    {{
      "tecnologia": "string - Nombre de la tecnología/modelo/herramienta",
      "frecuencia": "number",
      "porcentaje": "number",
      "contexto_uso": "string - Para qué la usan típicamente"
    }}
  ],
  
  "patrones_por_dominio": [
    {{
      "dominio": "string - Área de aplicación",
      "cantidad_proyectos": "number",
      "caracteristicas_comunes": ["lista de características"],
      "decisiones_tipicas": ["lista de decisiones típicas de este dominio"]
    }}
  ],
  
  "evaluacion_rubrica_agregada": [
    {{
      "criterio": "string - Criterio de la rúbrica",
      "proyectos_excelentes": "number",
      "proyectos_buenos": "number",
      "proyectos_regulares": "number",
      "proyectos_insuficientes": "number",
      "fortaleza_recurrente": "string - Qué hacen bien la mayoría",
      "debilidad_recurrente": "string - Donde fallan comúnmente",
      "recomendacion": "string - Consejo para mejorar en próximas entregas"
    }}
  ],
  
  "gaps_frecuentes": [
    {{
      "gap": "string - Aspecto faltante o débil",
      "frecuencia": "number - Cantidad de proyectos afectados",
      "gravedad": "string - alta/media/baja",
      "impacto_rubrica": "string - Cómo afecta la evaluación",
      "sugerencia_mejora": "string - Cómo podrían mejorarlo"
    }}
  ],
  
  "mejores_practicas_identificadas": [
    {{
      "practica": "string - Descripción de la mejor práctica",
      "proyectos_ejemplo": ["lista de proyectos que la implementan bien"],
      "por_que_destacable": "string - Por qué es una buena práctica"
    }}
  ],
  
  "riesgos_mas_identificados": [
    {{
      "riesgo": "string - Tipo de riesgo",
      "frecuencia": "number",
      "enfoques_mitigacion": ["lista de enfoques distintos de mitigación"]
    }}
  ],
  
  "insights_clave": [
    "string - Lista de insights importantes y accionables para retroalimentación"
  ],
  
  "recomendaciones_generales": [
    "string - Recomendaciones para la próxima entrega basadas en el análisis"
  ]
}}

# INSTRUCCIONES IMPORTANTES

1. Sé cuantitativo: incluye siempre frecuencias y porcentajes
2. Identifica tanto fortalezas como debilidades de manera equilibrada
3. Prioriza insights accionables que ayuden a mejorar la enseñanza
4. Los "gaps frecuentes" deben estar mapeados a criterios de la rúbrica
5. Las recomendaciones deben ser concretas y específicas
6. El output debe ser ÚNICAMENTE el JSON, sin texto adicional

Genera el análisis consolidado ahora:"""


def build_summary_report_prompt(consolidado: Dict) -> str:
    """
    Construye el prompt para generar un reporte ejecutivo en Markdown.
    
    Args:
        consolidado: Diccionario con el análisis consolidado de Fase 2
        
    Returns:
        Prompt para generar el reporte en formato Markdown
    """
    import json
    consolidado_json = json.dumps(consolidado, indent=2, ensure_ascii=False)
    
    return f"""Eres un asistente que genera reportes ejecutivos claros y accionables.

# DATOS DEL ANÁLISIS CONSOLIDADO
{consolidado_json}

# TU TAREA

Genera un reporte ejecutivo en formato Markdown que sea claro, escaneable y accionable
para el profesor/evaluador de estos proyectos.

# ESTRUCTURA DEL REPORTE

El reporte debe seguir esta estructura:

```markdown
# Reporte de Análisis - Entrega [Número]

## Resumen Ejecutivo
[2-3 párrafos con los hallazgos más importantes]

## Cumplimiento de Objetivos
[Análisis de cómo los proyectos cumplieron con el enunciado y rúbrica]

## Decisiones y Patrones Comunes

### Decisiones Técnicas Más Frecuentes
[Tabla o lista con decisiones técnicas y sus frecuencias]

### Decisiones de Negocio Más Frecuentes
[Tabla o lista con decisiones de negocio]

### Patrones por Dominio
[Análisis de patrones según área de aplicación]

## Áreas de Oportunidad

### Gaps Frecuentes
[Lista de aspectos débiles comunes con frecuencias]

### Errores Conceptuales Recurrentes
[Identificación de malentendidos o errores comunes]

## Mejores Prácticas Identificadas
[Lista de prácticas destacables que otros pueden replicar]

## Análisis por Criterio de Rúbrica
[Para cada criterio de la rúbrica: distribución de desempeño y recomendaciones]

## Insights Clave
[Bullets con los insights más importantes y accionables]

## Recomendaciones para Próxima Entrega
[Lista concreta de recomendaciones para mejorar]

---
*Generado automáticamente - Revisar y ajustar según necesidad*
```

# INSTRUCCIONES

1. No uses emojis
2. Incluye tablas donde sea apropiado (Markdown tables)
3. Usa negritas para datos clave y números importantes
4. Sé conciso pero completo
5. Enfócate en lo ACCIONABLE
6. El tono debe ser profesional pero amigable
7. Genera SOLO el Markdown, sin meta-comentarios

Genera el reporte ahora:"""