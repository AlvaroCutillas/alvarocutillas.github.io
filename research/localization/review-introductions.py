from pathlib import Path
from bs4 import BeautifulSoup
import json
ROOT=Path(__file__).parent;SITE=Path('C:/Users/acuth/Desktop/portfolio')
file=ROOT/'manual.es.json';manual=json.loads(file.read_text(encoding='utf-8'))
introductions={
'black-scholes-basics':[
'Black–Scholes–Merton relaciona el precio de una opción con el coste de replicar su pago. Las opciones europeas permiten obtener una fórmula explícita. Las americanas incorporan una decisión de parada óptima: ¿cuándo vale más ejercer que conservar el derecho?',
'Estos apuntes desarrollan esa relación desde los contratos y el arbitraje hasta el cálculo estocástico, la valoración, la cobertura y los métodos numéricos. El objetivo es interpretar cada fórmula principal: qué significan sus parámetros, por qué aparecen sus términos, qué supuestos la justifican y qué cambia cuando dejan de cumplirse. «Europea» y «americana» describen las reglas de ejercicio, no el mercado ni el país donde se negocia el contrato.'],
'black-scholes':[
'El proyecto estudia si una implementación de Black–Scholes sin dividendos valora de forma coherente las opciones europeas, si sus griegas se verifican mediante diferenciación numérica y si la incertidumbre de Monte Carlo se comporta como predice la teoría.'],
'equity-factor-model':[
'Un modelo de factores de renta variable representa las rentabilidades de muchas acciones mediante un conjunto reducido de influencias comunes. Puede describir el riesgo, atribuir resultados, contrastar restricciones de valoración de activos o ayudar a construir carteras. Estas aplicaciones comparten herramientas matemáticas, pero responden a preguntas distintas.'],
'implied-volatility-surface':[
'Una superficie de volatilidad implícita expresa un conjunto de precios de opciones europeas en un sistema común de coordenadas. Su construcción es un problema inverso, un problema de estimación estadística y un problema de coherencia económica.'],
'markowitz-portfolio-theory':[
'La teoría de carteras de Markowitz convierte la diversificación en un problema explícito de optimización: combinar activos para alcanzar una rentabilidad esperada con la menor varianza posible, o elegir una combinación eficiente de ambas magnitudes.',
'La idea central es que la contribución de un activo al riesgo de la cartera depende de cómo se mueve su rentabilidad respecto a la de las otras posiciones. Una cartera no se evalúa promediando las volatilidades de sus componentes. Los pesos interactúan con una matriz de covarianzas, y esas interacciones determinan qué combinaciones son eficientes.'],
'monte-carlo-option-pricing':[
'La valoración de opciones mediante Monte Carlo sustituye una esperanza difícil de evaluar por una media de flujos de caja simulados y descontados. Su utilidad depende de los contratos que permite representar; su fiabilidad, de una evaluación cuidadosa de la incertidumbre.'],
'systematic-trading-strategy':[
'Una estrategia sistemática es un proceso de decisión especificado: qué información observa, cómo construye las posiciones, cómo ejecuta las operaciones y cómo mide sus resultados económicos.'],
'var-expected-shortfall':[
'El valor en riesgo identifica un umbral de pérdidas. La pérdida esperada en cola describe la gravedad de las pérdidas más allá de ese umbral. Para comprender ambas medidas se necesita un modelo probabilístico, una regla de valoración y una definición precisa de la pérdida que se mide.'],
'yield-curve-modelling':[
'Una curva de tipos describe cómo depende de la fecha de pago el valor actual de una unidad monetaria futura. Construirla es un problema inverso de valoración: inferir factores de descuento a partir de un conjunto finito de instrumentos y definir una regla justificada entre sus vencimientos y más allá de ellos.',
'En los proyectos de valoración de opciones, los factores de descuento y los tipos de financiación eran parámetros de entrada. Aquí son las magnitudes que se estiman. Un tipo constante puede servir para una primera derivación, pero un bono con cupón, un swap de tipos y una opción a largo plazo muestran por qué cada fecha de pago puede requerir un descuento diferente. El objeto central es una función, no un único número llamado «tipo de interés».']
}
for name,spanish in introductions.items():
    soup=BeautifulSoup((SITE/'projects'/f'{name}.html').read_text(encoding='utf-8'),'html.parser')
    paras=soup.select('article>section:first-child>p')
    for p,translation in zip(paras,spanish):
        assert not p.select('a,math'),(name,'Introduction contains separate text units')
        manual[p.get_text(' ',strip=True)]=translation
file.write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8')
print('Reviewed study introductions saved.')
