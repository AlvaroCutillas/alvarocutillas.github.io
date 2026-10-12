"""Reviewed Spanish chapter titles, indexed against the unchanged English page."""
from pathlib import Path
from bs4 import BeautifulSoup
import json
ROOT=Path(__file__).parent
SITE=Path('C:/Users/acuth/Desktop/portfolio')
titles={
'black-scholes-basics':'''Introducción y alcance
Contratos de opciones, pagos y notación
Cotas de ausencia de arbitraje y paridad put-call
El modelo de Black–Scholes–Merton
Derivación de la ecuación de Black–Scholes–Merton
Valoración neutral al riesgo y representación de Feynman–Kac
Fórmulas de valoración de calls y puts europeas
Casos límite y estática comparativa
Sensibilidades de las opciones y griegas
Cobertura delta y error de replicación
Valoración de opciones europeas: ejemplo numérico
Volatilidad implícita: definición y estimación
Extensiones del marco de valoración europeo
Opciones americanas y parada óptima
Condiciones para el ejercicio anticipado
El problema de frontera libre y la put americana perpetua
El modelo binomial de Cox–Ross–Rubinstein
Métodos de diferencias finitas para valorar opciones
Valoración Monte Carlo y método de Longstaff–Schwartz
Valoración de opciones americanas: ejemplos numéricos
Valoración interactiva y análisis de sensibilidades
Implementación numérica y verificación
Limitaciones del modelo y especificaciones alternativas
Apéndice: derivaciones matemáticas e identidades
Ejercicios y soluciones
Referencias y lecturas adicionales''',
'black-scholes':'''¿Se puede validar rigurosamente un modelo sencillo?
El modelo: del proceso al precio
Qué miden las cinco griegas
Obtención de la volatilidad implícita
Monte Carlo como método independiente de valoración
La precisión mejora; el error observado no siempre
Cómo afectan los parámetros al valor de una opción
Comprobaciones distintas para detectar fallos diferentes
Fiabilidad, supuestos y limitaciones de mercado
Cómo revisar y reproducir la investigación
Un modelo de referencia con límites explícitos''',
'equity-factor-model':'''Introducción y alcance matemático
Rentabilidades, rentabilidades en exceso y unidades de los factores
Representaciones lineales de factores y sus distintos objetivos
Beta de mercado y modelo de valoración de activos financieros
Valoración multifactorial, APT y factores de descuento estocásticos
Fama–French, Carhart y modelos empíricos de referencia
Características de valor y carteras basadas en valoración
Momentum, ventanas de formación y efectos de reversión
Calidad, rentabilidad empresarial y características compuestas
Baja volatilidad, beta reducida y carteras defensivas
Datos disponibles en cada fecha, universo de inversión y sesgos
Transformación, winsorización y estandarización de descriptores
Clasificación de carteras, ponderación y restricciones de neutralidad
Regresión transversal y estimación de rentabilidades factoriales
Coeficientes de información y validación transversal
Atribución de series temporales y mínimos cuadrados ordinarios
Errores estándar, inferencia HAC y pruebas de valoración
Factores omitidos, colinealidad e identificación
Estimaciones móviles, regímenes y exposiciones condicionales
Validación cronológica y comparación de modelos
Covarianza de factores y modelos de riesgo específico
Contribuciones al riesgo, diversificación y cobertura de factores
Factores estadísticos, PCA y contracción de covarianzas
Regularización, estimación robusta e incertidumbre del modelo
Implementación de carteras, costes y gobernanza de la investigación
Laboratorio interactivo de atribución y construcción de carteras
Ejemplos de atribución, señales y riesgo
Apéndice matemático e implementación de referencia
Ejercicios y soluciones desarrolladas
Referencias y lecturas adicionales''',
'implied-volatility-surface':'''Introducción y alcance matemático
Valoración de opciones europeas a partir del precio forward
Volatilidad implícita: existencia y unicidad
Inversión numérica y condicionamiento
Coordenadas de moneyness, delta y varianza total
Sonrisas, asimetrías de volatilidad e interpretación económica
Estructura de vencimientos y varianza forward
Cadenas de opciones y convenciones contractuales
Estimación del forward, dividendos y paridad put-call
Filtrado de cotizaciones, intervalos bid-ask e incertidumbre
Arbitraje entre strikes: cotas, spreads verticales y mariposas
Ordenación por vencimientos con coste de mantenimiento determinista
Densidad neutral al riesgo y derivadas de la sonrisa
Interpolación, suavizado y regularidad de la superficie
La parametrización SVI de la varianza total
SSVI y parametrización coherente de los vencimientos
Objetivos de calibración y ponderación estadística
Optimización, identificabilidad y estabilidad de parámetros
Validación y certificación de ausencia de arbitraje estático
Comportamiento asintótico de las alas y riesgo de extrapolación
Volatilidad local de Dupire y estabilidad de las derivadas
Volatilidad estocástica, saltos y SABR
Sensibilidades de la superficie y convenciones de movimiento
Eventos programados, dividendos y modalidades de ejercicio
Proceso de implementación, seguimiento y riesgo de modelo
Laboratorio interactivo de superficies e inversión
Estudios numéricos y resultados de calibración
Apéndice matemático e implementación de referencia
Ejercicios y soluciones desarrolladas
Referencias y lecturas adicionales''',
'markowitz-portfolio-theory':'''Introducción y alcance
Rentabilidades y contabilidad de carteras
Rentabilidad esperada y agregación lineal
Varianza, covarianza y correlación
Representación matricial y admisibilidad
Diversificación con dos activos
Límites de la diversificación y dependencia factorial
Eficiencia media-varianza y carteras factibles
Preferencias, utilidad y supuestos del modelo
Formulaciones de optimización media-varianza
Multiplicadores de Lagrange y condiciones de primer orden
La cartera global de mínima varianza
La frontera eficiente analítica
Pesos de la frontera y separación en dos fondos
El activo libre de riesgo y la asignación de capital
La cartera tangente y el ratio de Sharpe
Aversión al riesgo y asignación óptima a activos de riesgo
Restricciones de posiciones largas y condiciones de optimalidad
Restricciones de exposición, concentración y rotación
Contribuciones marginales y componentes del riesgo
Estimación de rentabilidades esperadas y covarianzas
Contracción de covarianzas y condicionamiento numérico
Incertidumbre de rentabilidades esperadas y optimización robusta
Rebalanceo y evaluación temporal
Laboratorio interactivo de la frontera eficiente
Ejemplos numéricos desarrollados
Implementación y verificación numérica
Apéndice matemático
Ejercicios y soluciones
Referencias y lecturas adicionales''',
'monte-carlo-option-pricing':'''Introducción y alcance
Valoración neutral al riesgo y simulación
Fundamentos de probabilidad y estadística
Estimadores Monte Carlo
Análisis del error e intervalos de confianza
Generación de números aleatorios y reproducibilidad
Simulación exacta del movimiento browniano geométrico
Valoración de opciones europeas
Convergencia y complejidad computacional
Discretización temporal y sesgo numérico
Variables antitéticas
Variables de control
Muestreo estratificado e hipercubo latino
Muestreo por importancia y eventos raros
Métodos cuasi-Monte Carlo
Monte Carlo multinivel
Activos correlacionados y opciones sobre cestas
Opciones asiáticas y otras opciones dependientes de la trayectoria
Opciones barrera y puentes brownianos
Estimación de sensibilidades mediante Monte Carlo
Opciones americanas y Monte Carlo de mínimos cuadrados
Validación, eficiencia y riesgo de modelo
Laboratorio interactivo de simulación
Ejemplos de valoración desarrollados
Implementación y verificación numérica
Apéndice matemático
Ejercicios y soluciones
Referencias y lecturas adicionales''',
'systematic-trading-strategy':'''Introducción y alcance de la investigación
Hipótesis económicas y especificaciones de la estrategia
Conjuntos de información y calendario de ejecución
Datos de mercado y universos disponibles en cada fecha
Rentabilidades, capitalización y referencias de comparación
Familias de señales y objetivos de predicción
Momentum de series temporales y filtros de tendencia
Reversión a la media y señales contrarias
Normalización de variables y modelos predictivos
Dimensionamiento de posiciones y objetivos de volatilidad
Construcción de carteras y restricciones de exposición
Costes de transacción y rotación
Ejecución, órdenes y supuestos de ejecución efectiva
Efectivo, posiciones y contabilidad autofinanciada
Motores de backtesting y orden de los eventos
Muestras de entrenamiento, validación y evaluación
Selección walk-forward y concatenación de rentabilidades
Etiquetas solapadas, purgado y periodos de separación
Sesgos de investigación y backtests engañosos
Contrastes múltiples y sobreajuste del backtest
Estadísticas de rendimiento y comparación con referencias
Ratios de Sharpe, dependencia e inferencia
Caídas desde máximos, pérdidas de cola y riesgo de trayectoria
Robustez, remuestreo y escenarios de estrés
Atribución, capacidad y seguimiento posterior
Laboratorio interactivo de estrategias sistemáticas
Ejemplos de estrategias y evaluación walk-forward
Implementación y apéndice matemático
Ejercicios y soluciones desarrolladas
Referencias y lecturas adicionales''',
'var-expected-shortfall':'''Introducción y alcance
Beneficios, pérdidas y horizonte de riesgo
Funciones de distribución y cuantiles
Valor en riesgo: definición e interpretación
Pérdida esperada en cola y masa de probabilidad
Coherencia y diversificación
Distribuciones normales de pérdidas
Distribuciones t de Student y colas pesadas
Agregación de carteras y dependencia
Escalado del horizonte y dependencia temporal
Simulación histórica y colas empíricas
Simulación histórica ponderada
Modelos paramétricos y delta-normal
Delta-gamma y revaloración completa
Estimación de riesgo mediante Monte Carlo
Filtrado de volatilidad y riesgo condicional
Teoría de valores extremos y extrapolación de colas
Dependencia de cola, estrés y liquidez
Riesgo marginal y contribuciones por componentes
Optimización de carteras con pérdida esperada en cola
Validación de pronósticos y contexto regulatorio
Cobertura incondicional y prueba de Kupiec
Independencia y cobertura condicional
Validación de la pérdida esperada en cola
Incertidumbre muestral e incertidumbre del modelo
Laboratorio interactivo de riesgo de cola
Ejemplos de valoración y riesgo
Implementación y apéndice matemático
Ejercicios y soluciones desarrolladas
Referencias y lecturas adicionales''',
'yield-curve-modelling':'''Introducción y alcance matemático
Factores de descuento y representación del valor presente
Tipos cupón cero y convenciones de capitalización
Tipos forward y estructura temporal integrada
Tipos a la par y TIR a vencimiento
Calendarios, cómputo de días y convenciones de cotización
Instrumentos de mercado y familias de curvas
Bootstrap de depósitos y activos cupón cero
Bootstrap de bonos con cupón y swaps a la par
Descuento, proyección y valoración multicurva
Interpolación de descuentos, tipos cero y forwards
Splines, suavizado y regularización
Coherencia económica y curvas de tipos admisibles
El modelo de estructura temporal de Nelson–Siegel
La extensión de Svensson y el segundo factor de curvatura
Objetivos de calibración y pesos de las observaciones
Proyección variable e identificación numérica
Análisis de residuos, validación e incertidumbre
Comportamiento en los extremos y extrapolación a largo plazo
Factores dinámicos, modelos afines y coherencia HJM
Duración y convexidad ante desplazamientos de la curva
Sensibilidades por tramo y riesgo de calibración
Carry forward, roll-down e interpretación económica
Escenarios de curvas y riesgo de componentes principales
Construcción reproducible y proceso de investigación
Laboratorio interactivo de estructuras temporales y bonos
Ejemplos de calibración y valoración
Apéndice matemático e implementación de referencia
Ejercicios y soluciones desarrolladas
Referencias y lecturas adicionales'''
}
manual=json.loads((ROOT/'manual.es.json').read_text(encoding='utf-8'))
count=0
for name,translation in titles.items():
    soup=BeautifulSoup((SITE/'projects'/f'{name}.html').read_text(encoding='utf-8'),'html.parser')
    english=[e.get_text(' ',strip=True) for e in soup.select('article>section>h2')]
    spanish=translation.splitlines()
    assert len(english)==len(spanish),(name,len(english),len(spanish))
    manual.update(zip(english,spanish));count+=len(english)
(ROOT/'manual.es.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{count} reviewed Spanish chapter titles saved.')
