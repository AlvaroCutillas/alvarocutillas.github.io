from pathlib import Path
import json,re
ROOT=Path(__file__).parent
file=ROOT/'manual.es.json'
d=json.loads(file.read_text(encoding='utf-8'))
checks=json.loads((ROOT/'laboratory-verification.json').read_text(encoding='utf-8'))['report']
translations={
'black-scholes-basics.html':[
'Sensibilidades de una call europea. CRR 400 aproxima ambos estilos de ejercicio; los valores analíticos europeos sirven de referencia para el modelo de difusión. Sin dividendos y con tipos no negativos, las calls americanas y europeas tienen el mismo valor en un mismo árbol.'
],
'equity-factor-model.html':[
'MCO en los meses 1–180; meses 181–240 reservados. 6 coeficientes, incluida una constante. Retardo HAC 6 con ponderaciones de Bartlett y ajuste T/(T−p). Cambiar el número de retardos modifica la incertidumbre, no los coeficientes. Los coeficientes quedan fijados antes de evaluar la muestra reservada.',
'Puntuación de valor; 20% en cada extremo. 32 posiciones largas y 32 posiciones cortas. Exposición bruta 2.00, peso neto 0.000000. Los pesos están equilibrados dentro de cada sector. Coste de entrada 20.00 pb. El IC utiliza la sección transversal completa de 160 acciones.',
'Todos los datos son sintéticos y están incluidos en la página. HAC utiliza ponderaciones de Bartlett y el ajuste T/(T−p). La atribución de varianza utiliza la covarianza de los factores centrados y la suma de cuadrados de los residuos, ambas divididas por T−1 para coincidir con la varianza de la muestra de entrenamiento. El experimento transversal solo aplica el coste de entrada; omite el préstamo de acciones, la financiación, las operaciones posteriores y el impacto de mercado. Las rentabilidades de las carteras se normalizan respecto a una unidad de capital declarada.'
],
'implied-volatility-surface.html':[
None,
'Volatilidad implícita Black obtenida: 22.248% · residuo de revaloración 0.00e+0 unidades de prima. Esta inversión mantiene fijos el contrato seleccionado y los parámetros de coste de mantenimiento.',
'SSVI sintético con phi(theta) = eta / (1 + theta) y una tasa de varianza ATM positiva y decreciente. Forward = spot × exp((rate − yield)T); D = exp(−rate T). Las celdas del mapa contienen valores muestreados, no observaciones interpoladas. La volatilidad local supone una difusión local europea suave y no está disponible cuando el diagnóstico del punto es inválido. Cambiar un parámetro de forma no equivale a calibrar una cadena de opciones de mercado.'
],
'markowitz-portfolio-theory.html':[
'Asignación para el objetivo exacto: tramo eficiente. Las carteras de riesgo permiten ventas en corto sin restricciones y tienen un presupuesto neto del 100%. La asignación de efectivo mostrada optimiza γ dentro de la combinación del fondo tangente seleccionado y efectivo, con el mismo tipo para prestar y endeudarse y sin restricciones al apalancamiento del fondo. Los parámetros son momentos supuestos; el gráfico no representa resultados observados ni intervalos de confianza de la estimación.'
],
'monte-carlo-option-pricing.html':[
'Simulación exacta del valor final del GBM. El error estándar estimado utiliza observaciones independientes del pago. Los intervalos sucesivos son aproximaciones normales puntuales al 95%; inspeccionarlos repetidamente no garantiza una cobertura simultánea.'
],
'systematic-trading-strategy.html':[
'Mercado sintético con cinco regímenes; semilla 5105. La evaluación común comienza en el cierre 64 e incluye 1448 periodos de rentabilidad. Un objetivo formado al cierre k se ejecuta al cierre k + 1 y recibe por primera vez la rentabilidad k + 2. 807 órdenes de rebalanceo con importe distinto de cero. Se supone que todas las ejecuciones se producen a precios de cierre sintéticos; los costes son proporcionales al nominal efectivamente negociado en cada sentido. Estos resultados son exploratorios; el Sharpe anualizado utiliza la convención de escalado IID.'
],
'var-expected-shortfall.html':[
'Pérdidas normales con la media y desviación estándar especificadas para el horizonte. 25,000 escenarios sintéticos; semilla 4104. El riesgo empírico utiliza la CDF inversa y una fracción de la masa en el umbral. Las curvas discontinuas corresponden a esta muestra concreta, no a un intervalo de confianza.'
],
'yield-curve-modelling.html':[
'D(0) = 1; todos los factores de descuento muestreados son positivos. Límite del tipo a corto plazo: 1.5000%. Límite del tipo a largo plazo: 3.5000%. Forward mínimo muestreado: 1.5000%. Todos los forwards muestreados son no negativos; la curva de descuento mostrada es decreciente.',
'Comparación con los parámetros actuales; estas cotizaciones todavía no se han ajustado en esta sesión. RMSE de entrenamiento: 0.725 pb. RMSE de la muestra reservada: 1.294 pb. Las cotizaciones reservadas nunca entran en el objetivo.',
'La TIR es nominal con 2 periodos de capitalización al año. Las curvas a la par utilizan cupones semestrales, independientemente de la frecuencia del bono seleccionado. Duración, convexidad y DV01 se refieren a un desplazamiento paralelo de los tipos cero continuos; DV01 es la pérdida positiva de primer orden para +1 pb. La calibración sintética utiliza ponderaciones iguales para los tipos cero, cotas de decaimiento τ₁ ∈ [0.15, 10], τ₂ ∈ [0.25, 30] años y |β| ≤ 15%. La búsqueda no garantiza un óptimo global. El CSV exporta la curva y los parámetros actuales.'
]}
for row in checks:
    for en,es in zip(row['en'],translations.get(row['file'],[])):
        if es:d[re.sub(r'\s+',' ',en).strip()]=es
d.update({
'Bootstrapping':'Bootstrap de la curva',
'SHORT END':'TRAMO CORTO','MATURITY':'VENCIMIENTO','LONG END':'TRAMO LARGO',
'Running intervals are pointwise 95% normal approximations; repeated inspection does not give a simultaneous coverage guarantee.':'Los intervalos sucesivos son aproximaciones normales puntuales al 95%; inspeccionarlos repetidamente no garantiza una cobertura simultánea.',
'Quality score':'Puntuación de calidad','Value score':'Puntuación de valor','Momentum score':'Puntuación de momentum','Low-volatility score':'Puntuación de baja volatilidad',
'Minimum sampled g =':'Mínimo muestreado de g =',
'Minimum sampled g = 0.31116; minimum sampled ∂w/∂T = 0.019800. Diagnostic grid: 61 maturities from 0.05 to 3 years and 401 k values from −3 to 3. Calendar sufficient condition passes analytically for this family.':'Mínimo muestreado de g = 0.31116; mínimo muestreado de ∂w/∂T = 0.019800. Malla de diagnóstico: 61 vencimientos desde 0.05 hasta 3 años y 401 valores de k desde −3 hasta 3. La condición suficiente de calendario se cumple analíticamente para esta familia.',
'Global test values: wing 3.7950, curvature 2.1821. Horizon values: wing 0.4215, curvature 0.8618. Required: wing < 4 and curvature ≤ 4.':'Valores de la prueba global: ala 3.7950, curvatura 2.1821. Valores del horizonte: ala 0.4215, curvatura 0.8618. Requisito: ala < 4 y curvatura ≤ 4.',
'; minimum sampled ∂w/∂T =':'; mínimo muestreado de ∂w/∂T =',
'Diagnostic grid:':'Malla de diagnóstico:',
'maturities from':'vencimientos desde','years and':'años y','k values from':'valores de k desde',
'Calendar sufficient condition passes analytically for this family.':'La condición suficiente de calendario se cumple analíticamente para esta familia.',
'Global test values: wing':'Valores de la prueba global: ala','Horizon values: wing':'Valores del horizonte: ala',
', curvature':', curvatura','Required: wing':'Requisito: ala','and curvature':'y curvatura',
'D(0) = 1; all sampled discount factors are positive. Short-rate limit:':'D(0) = 1; todos los factores de descuento muestreados son positivos. Límite del tipo a corto plazo:',
'Long-rate limit:':'Límite del tipo a largo plazo:','Minimum sampled forward:':'Forward mínimo muestreado:',
'All sampled forwards are nonnegative; the displayed discount curve is decreasing.':'Todos los forwards muestreados son no negativos; la curva de descuento mostrada es decreciente.',
'Negative forwards are present: this is a negative-rate curve assumption, not an automatic arbitrage diagnosis.':'Hay forwards negativos: se está suponiendo una curva con tipos negativos; esto no implica automáticamente que exista arbitraje.',
'Current parameter comparison; these quotes have not been fitted in this session.':'Comparación con los parámetros actuales; estas cotizaciones todavía no se han ajustado en esta sesión.',
'Synthetic five-regime market; seed':'Mercado sintético con cinco regímenes; semilla',
'Common evaluation starts at close':'La evaluación común comienza en el cierre',
'nonzero rebalance orders.':'órdenes de rebalanceo con importe distinto de cero.',
'All fills are assumed at synthetic closes; costs are proportional to actual one-way notional. These are exploratory results; the annualized Sharpe uses the IID scaling convention.':'Se supone que todas las ejecuciones se producen a precios de cierre sintéticos; los costes son proporcionales al nominal efectivamente negociado en cada sentido. Estos resultados son exploratorios; el Sharpe anualizado utiliza la convención de escalado IID.',
'synthetic scenarios; seed':'escenarios sintéticos; semilla',
'Empirical risk uses the inverse CDF and fractional boundary mass. Dashed curves show this one sample, not a confidence interval.':'El riesgo empírico utiliza la CDF inversa y una fracción de la masa en el umbral. Las curvas discontinuas corresponden a esta muestra concreta, no a un intervalo de confianza.',
'Exact-target allocation:':'Asignación para el objetivo exacto:',
'The shown cash allocation optimises γ within the chosen tangency fund plus cash, with equal borrowing and lending rates and unrestricted fund leverage. Inputs are assumed moments; the chart does not represent realised outcomes or estimation confidence intervals.':'La asignación de efectivo mostrada optimiza γ dentro de la combinación del fondo tangente seleccionado y efectivo, con el mismo tipo para prestar y endeudarse y sin restricciones al apalancamiento del fondo. Los parámetros son momentos supuestos; el gráfico no representa resultados observados ni intervalos de confianza de la estimación.',
})
titles={
'black-scholes-basics.html':'Black–Scholes: valoración de opciones',
'equity-factor-model.html':'Modelo de factores de renta variable',
'implied-volatility-surface.html':'Superficie de volatilidad implícita',
'markowitz-portfolio-theory.html':'Markowitz: teoría de carteras',
'monte-carlo-option-pricing.html':'Monte Carlo: valoración de opciones',
'systematic-trading-strategy.html':'Estrategia de trading sistemático',
'var-expected-shortfall.html':'Valor en riesgo y pérdida esperada en cola',
'yield-curve-modelling.html':'Modelización de la curva de tipos'
}
source=json.loads((ROOT/'page-texts.json').read_text(encoding='utf-8'))
for name,title in titles.items():
    d[source[name]['values'][0]]=title+' · Fundamentos quant — Álvaro Cutillas'
# Exact numeric UI entries should retain the financial unit consistently.
for page in json.loads((ROOT/'page-texts.json').read_text(encoding='utf-8')).values():
    for key in page['values']:
        if re.fullmatch(r'[-+0-9.,eE %]+ bp',key):d[key]=key[:-2]+'pb'
file.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('Default laboratory notes and financial units reviewed.')
