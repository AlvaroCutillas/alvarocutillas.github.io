from pathlib import Path
from bs4 import BeautifulSoup
import json
ROOT=Path(__file__).parent;SITE=Path('C:/Users/acuth/Desktop/portfolio')
manual=json.loads((ROOT/'manual.es.json').read_text(encoding='utf-8'))
translations={
'black-scholes-basics':[
'De la replicación europea al ejercicio óptimo de opciones americanas. Apuntes completos sobre el modelo, sus fundamentos matemáticos y sus límites.',
'Derivaciones, intuición, fórmulas y gráficos calculados en un recorrido de estudio. Comienza con el contrato y llega hasta la frontera de ejercicio.'],
'black-scholes':[
'Un modelo de valoración con solución analítica resulta útil cuando se pueden explicar sus convenciones, sensibilidades y comprobaciones numéricas. Este proyecto desarrolla esos elementos y mide dónde coincide la simulación con la solución analítica y dónde aparecen diferencias.',
'Un estudio reproducible en Python con un ejemplo sintético. La página muestra cálculos obtenidos al ejecutar el código del proyecto; no utiliza cotizaciones de mercado ni presenta una estrategia empírica de trading.'],
'equity-factor-model':[
'De las características de las acciones a los factores comunes de rentabilidad. Apuntes completos sobre estilos de renta variable, estimación de factores y riesgo de cartera.',
'Teoría, intuición y ejemplos calculados en un recorrido de estudio. Construye la señal, estima la exposición y distingue entre atribución y predicción.'],
'implied-volatility-surface':[
'De las primas de las opciones a sonrisas coherentes entre precios de ejercicio y vencimientos. Apuntes completos sobre inversión, calibración y sus condiciones matemáticas de consistencia.',
'Derivaciones, intuición económica y ejemplos calculados en un recorrido de estudio. Convierte precios en volatilidades, ajusta la superficie y examina los riesgos que revelan sus derivadas.'],
'markowitz-portfolio-theory':[
'De la covarianza y la diversificación a la frontera eficiente. Apuntes completos sobre selección de carteras, restricciones e incertidumbre de los parámetros.',
'Derivaciones, intuición práctica y ejemplos calculados en un recorrido de estudio. Comprende cómo se combinan los activos, qué hace eficiente a una cartera y cómo influye la estimación.'],
'monte-carlo-option-pricing':[
'De las esperanzas neutrales al riesgo a los flujos de caja simulados. Apuntes completos sobre valoración, incertidumbre estadística y estimación eficiente.',
'Fundamentos matemáticos, intuición práctica y experimentos calculados en un recorrido de estudio. Aprende a estimar un valor, medir su incertidumbre y mejorar el cálculo.'],
'portfolio-optimization':[
'Fronteras eficientes, estimación robusta de covarianzas y construcción de carteras fuera de muestra.',
'¿Qué parece óptimo al estimarlo con datos históricos? ¿Cuánto de ese resultado resiste la incertidumbre de los parámetros, la concentración, los costes de negociación y una prueba estrictamente cronológica?'],
'systematic-trading-strategy':[
'De las señales de trading a una cartera autofinanciada. Apuntes completos sobre diseño de estrategias, ejecución y evaluación rigurosa de resultados.',
'Intuición económica, fórmulas y experimentos calculados en un recorrido de estudio. Define la información disponible, modeliza las operaciones y evalúa el resultado después de costes.'],
'var-expected-shortfall':[
'De los cuantiles de pérdidas a la gravedad de los resultados extremos. Apuntes completos sobre medición del riesgo de cola, estimación y validación de pronósticos.',
'Definiciones, derivaciones y ejemplos calculados en un recorrido de estudio. Comprende qué indica el umbral, qué sucede más allá de él y qué evidencia respalda la estimación.'],
'yield-curve-modelling':[
'De los factores de descuento a estructuras temporales coherentes. Apuntes completos sobre construcción de curvas, calibración paramétrica y riesgo de renta fija.',
'Derivaciones, intuición económica y ejemplos calculados en un recorrido de estudio. Construye la curva, ajusta su forma y comprende qué información aportan sus tipos de interés.']
}
for name,spanish in translations.items():
    soup=BeautifulSoup((SITE/'projects'/f'{name}.html').read_text(encoding='utf-8'),'html.parser')
    english=[e.get_text(' ',strip=True) for e in soup.select('.hero .lede,.hero .context')]
    assert len(english)==len(spanish)
    manual.update(zip(english,spanish))
manual.update({
'Attribution model':'Modelo de atribución',
'Generating market exposure':'Exposición de mercado simulada',
'Generating value exposure':'Exposición al factor valor simulada',
'Generating momentum exposure':'Exposición a momentum simulada',
'Generating quality exposure':'Exposición al factor calidad simulada',
'Generating low-vol exposure':'Exposición a baja volatilidad simulada',
'Generating monthly alpha (bps)':'Alfa mensual simulado (pb)',
'Innovation base scale (%)':'Escala base de las innovaciones (%)',
'Training months':'Meses de entrenamiento',
'Training R²':'R² de entrenamiento',
'Training monthly volatility':'Volatilidad mensual de entrenamiento',
'HAC lag count':'Número de retardos HAC',
'Systematic variance share':'Proporción de varianza sistemática',
'Withheld mean residual':'Residuo medio de la muestra reservada',
'Estimated monthly alpha':'Alfa mensual estimado',
'Alpha HAC t-statistic':'Estadístico t HAC del alfa',
'Withheld monthly RMSE':'RMSE mensual de la muestra reservada',
'Formation characteristic':'Característica de formación',
'Tail size (%)':'Tamaño de cada extremo (%)',
'Sector construction':'Construcción por sectores',
'One-way entry cost (bps)':'Coste de entrada por operación (pb)',
'Gross next-month return':'Rentabilidad bruta del mes siguiente',
'After entry cost':'Después del coste de entrada',
'Pearson information coefficient':'Coeficiente de información de Pearson',
'Rank information coefficient':'Coeficiente de información por rangos',
'Sector-balanced tails':'Extremos equilibrados por sector',
'Unrestricted tails':'Extremos sin restricciones',
'Equity factor laboratory':'Laboratorio de factores de renta variable',
'240 synthetic months / 160-stock snapshot':'240 meses sintéticos / 160 acciones',
'Withheld monthly excess returns':'Rentabilidades mensuales en exceso de la muestra reservada',
'Withheld cumulative arithmetic return':'Rentabilidad aritmética acumulada de la muestra reservada',
'Formation-score decile outcomes':'Resultados por deciles de la puntuación de formación',
'Derivative':'Derivada',
'Recovered call IV':'Volatilidad implícita de la call obtenida',
'Recovered Black IV':'Volatilidad implícita Black obtenida',
'Sticky strike':'Strike constante',
'Sticky strike delta':'Delta con strike constante',
'The ATM skew satisfies':'La asimetría ATM satisface',
'Black':'Black',
'Turnover':'Rotación',
'Figure':'Figura',
'Figures':'Figuras',
'Derivations':'Derivaciones',
'Forward / strike':'Forward / precio de ejercicio',
'Matched training-sample variance attribution; signed contributions can be negative':'Atribución de la varianza muestral de entrenamiento; las contribuciones pueden ser negativas',
'Signed characteristic and sector weights; these are not time-series factor betas':'Exposiciones firmadas a características y sectores; no son betas factoriales de series temporales',
'OLS exposures and inference; alpha is displayed in basis points per month':'Exposiciones MCO e inferencia; el alfa se expresa en puntos básicos por mes'
})
(ROOT/'manual.es.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
print('Reviewed hero and laboratory terminology saved.')
