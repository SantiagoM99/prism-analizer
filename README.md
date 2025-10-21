# Prism Analizer
Sistema automatizado para extraer decisiones, identificar patrones y generar  insights accionables desde proyectos académicos de aplicaciones LLM usando Gemini AI.

## 📋 Características

- **Extracción Estructurada**: Procesa markdowns de proyectos y extrae información estructurada según enunciado y rúbrica
- **Análisis Consolidado**: Identifica patrones, decisiones comunes, fortalezas y debilidades agregadas
- **Múltiples Outputs**: Genera JSON, CSV y reportes ejecutivos en Markdown
- **Modular y Reutilizable**: Fácil de configurar para diferentes entregas
- **Logging Completo**: Trazabilidad total del proceso de análisis

## 🚀 Instalación

### 1. Clonar/Descargar el proyecto

```bash
git clone <tu-repo>
cd analizador-proyectos-llm
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Mac/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar API Key

1. Obtén tu API key de Gemini en: https://aistudio.google.com/app/apikey
2. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edita `.env` y agrega tu API key:
   ```
   GEMINI_API_KEY=tu_api_key_real_aqui
   ```

## 📁 Estructura del Proyecto

```
analizador-proyectos-llm/
├── config.py              # Configuración por entrega
├── prompts.py             # Templates de prompts para Gemini
├── extractor.py           # Fase 1: Extracción individual
├── consolidator.py        # Fase 2: Análisis consolidado
├── utils.py               # Utilidades generales
├── main.py                # Script principal
├── requirements.txt       # Dependencias
├── .env                   # Variables de entorno (NO commitear)
├── .env.example           # Plantilla de .env
└── entregas/              # Directorio de entregas
    └── entrega1/
        ├── enunciado.md
        ├── rubrica.md
        ├── proyectos/
        │   ├── proyecto1.md
        │   ├── proyecto2.md
        │   └── ...
        └── resultados/    # Se genera automáticamente
```

## ⚙️ Configuración para Nueva Entrega

### 1. Crear estructura de directorio

```bash
mkdir -p entregas/entrega1/proyectos
```

### 2. Agregar archivos requeridos

- `entregas/entrega1/enunciado.md` - Enunciado de la actividad
- `entregas/entrega1/rubrica.md` - Rúbrica de evaluación
- `entregas/entrega1/proyectos/*.md` - Markdowns de proyectos (40 archivos)

### 3. Configurar en `config.py`

Edita `config.py` y agrega la configuración:

```python
ENTREGA_1_CONFIG = EntregaConfig(
    numero_entrega=1,
    enunciado_path=Path("./entregas/entrega1/enunciado.md"),
    rubrica_path=Path("./entregas/entrega1/rubrica.md"),
    proyectos_dir=Path("./entregas/entrega1/proyectos"),
    output_dir=Path("./entregas/entrega1/resultados")
)
```

Y agrégala al diccionario en `get_config_for_entrega()`.

## 🎯 Uso

### Ejecución Básica

```bash
python main.py 1
```

Donde `1` es el número de entrega que quieres procesar.

### Ejecución Interactiva

Si no pasas el número de entrega, el script te lo preguntará:

```bash
python main.py
```

### Proceso Completo

El script ejecuta automáticamente:

1. **Fase 1**: Extracción individual de cada proyecto (40 llamadas a Gemini)
2. **Fase 2**: Consolidación y análisis agregado (2-3 llamadas a Gemini)
3. **Generación de Reportes**: CSV, JSON y Markdown

## 📊 Outputs Generados

Al finalizar, encontrarás en `entregas/entregaX/resultados/`:

```
resultados/
├── fase1_extracciones/
│   ├── proyecto1_extraction.json
│   ├── proyecto2_extraction.json
│   └── ... (un JSON por proyecto)
├── fase2_consolidado/
│   ├── analisis_consolidado.json      # Análisis agregado completo
│   ├── decisiones_consolidadas.csv    # Tabla de decisiones
│   └── reporte_ejecutivo.md           # Reporte legible para humanos
├── logs/
│   └── analisis_YYYYMMDD_HHMMSS.log  # Log detallado
└── resumen_ejecucion.json             # Resumen de la ejecución
```

### Archivos Principales

1. **`decisiones_consolidadas.csv`**: Tabla con todas las decisiones extraídas
   - Columnas: Proyecto, Dominio, Categoría, Tipo, Decisión
   - Útil para análisis en Excel/Google Sheets

2. **`reporte_ejecutivo.md`**: Reporte legible con:
   - Resumen ejecutivo
   - Decisiones y patrones comunes
   - Áreas de oportunidad y gaps frecuentes
   - Mejores prácticas identificadas
   - Análisis por criterio de rúbrica
   - Recomendaciones para próxima entrega

3. **`analisis_consolidado.json`**: Datos estructurados completos
   - Para procesamiento programático adicional
   - Incluye frecuencias, porcentajes, ejemplos

## 🔧 Personalización

### Cambiar Modelo de Gemini

En `config.py`, modifica:

```python
model_name: str = "gemini-2.0-flash-exp"  # Cambia a otro modelo si necesitas
```

Modelos disponibles:
- `gemini-2.0-flash-exp` (recomendado: rápido y económico)
- `gemini-1.5-pro` (más potente, más costoso)
- `gemini-1.5-flash` (alternativa rápida)

### Ajustar Temperatura

En `config.py`:

```python
temperature: float = 0.1  # Más bajo = más determinístico
```

- **0.0 - 0.2**: Recomendado para extracción estructurada
- **0.3 - 0.5**: Para análisis más creativos
- **0.6 - 1.0**: Más variación (no recomendado para este caso)

### Modificar Prompts

Edita `prompts.py` para ajustar:
- `build_extraction_prompt()`: Fase 1 - Extracción individual
- `build_consolidation_prompt()`: Fase 2 - Análisis consolidado
- `build_summary_report_prompt()`: Generación de reporte MD

## 📈 Estimación de Costos

Con Gemini 2.0 Flash (recomendado):

- **Input**: $0.075 por 1M tokens
- **Output**: $0.30 por 1M tokens

### Ejemplo para 40 proyectos:

Asumiendo:
- Cada proyecto: ~3,000 tokens (markdown + enunciado + rúbrica)
- Output por proyecto: ~2,000 tokens

**Fase 1** (40 llamadas):
- Input: 40 × 3,000 = 120,000 tokens ≈ $0.009
- Output: 40 × 2,000 = 80,000 tokens ≈ $0.024

**Fase 2** (2-3 llamadas):
- Input: ~100,000 tokens ≈ $0.0075
- Output: ~20,000 tokens ≈ $0.006

**Total estimado por entrega: ~$0.05 USD** 💰

> Nota: Costos pueden variar. Verifica precios actuales en: https://ai.google.dev/pricing

## 🐛 Troubleshooting

### Error: "No se encontró GEMINI_API_KEY"

- Verifica que creaste el archivo `.env` (no `.env.example`)
- Confirma que agregaste tu API key en el formato correcto
- Asegúrate de estar en el directorio correcto al ejecutar

### Error: "Archivo no encontrado"

- Verifica que las rutas en `config.py` sean correctas
- Asegúrate de que `enunciado.md` y `rubrica.md` existan
- Confirma que el directorio `proyectos/` contenga archivos `.md`

### JSON inválido en respuestas

- El sistema tiene reintentos automáticos (configurable con `max_retries`)
- Revisa los logs en `resultados/logs/` para ver el error específico
- Considera aumentar `temperature` levemente si las respuestas son muy cortadas

### Rate Limits de la API

Si obtienes errores de rate limit:
- El script tiene pausas automáticas entre proyectos (1 segundo)
- Puedes aumentar la pausa editando `extractor.py` línea `time.sleep(1)`
- Considera usar un modelo con mayores límites (Vertex AI vs AI Studio)

## 🔐 Seguridad

- **NUNCA** commitees el archivo `.env` con tu API key
- Agrega `.env` a `.gitignore`
- No compartas tus API keys públicamente
- Revoca y regenera keys si se exponen accidentalmente

## 📝 Logging

Los logs incluyen:
- Progreso de procesamiento por proyecto
- Errores y warnings detallados
- Estimación de tokens por proyecto
- Tiempos de respuesta de la API
- Resumen de éxito/fallos

Ubicación: `entregas/entregaX/resultados/logs/analisis_TIMESTAMP.log`

## 🤝 Contribuir

Si quieres mejorar el sistema:

1. Haz un fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/mejora`
3. Commit tus cambios: `git commit -am 'Agrega nueva funcionalidad'`
4. Push a la rama: `git push origin feature/mejora`
5. Crea un Pull Request

## 📄 Licencia

[Especifica tu licencia aquí - MIT, Apache 2.0, etc.]

## 👥 Autores

[Tu nombre / Equipo]

## 🙏 Agradecimientos

- Google Gemini AI por la API
- Anthropic Claude por asistencia en desarrollo

---

## 🎓 Uso Académico

Este sistema está diseñado para facilitar la evaluación de proyectos estudiantiles. Recomendaciones:

1. **Validación Humana**: Siempre revisa los resultados antes de usarlos para evaluación formal
2. **Transparencia**: Informa a los estudiantes que se usa IA para análisis preliminar
3. **Iteración**: Usa los insights para mejorar el diseño de próximas entregas
4. **Retroalimentación**: El reporte generado puede servir como base para feedback grupal

## 📞 Soporte

Para preguntas o problemas:
- Revisa la sección de Troubleshooting
- Consulta los logs en `resultados/logs/`
- [Agrega tu método de contacto preferido]

---

**¿Listo para analizar proyectos? 🚀**

```bash
python main.py 1
```