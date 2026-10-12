"""Context-aware terminology corrections for the offline Spanish catalogue."""
import re
def polish(en,es):
    def replace(pattern,value):
        nonlocal es
        es=re.sub(pattern,value,es,flags=re.I)
    replace(r'\bcostos\b','costes')
    replace(r'series cronológicas','series temporales')
    if 'greeks' in en.lower():replace(r'\bgriegos\b','griegas')
    if 'derivations' in en.lower():replace(r'\bderivados\b','derivaciones')
    if 'inputs' in en.lower():replace(r'\binsumos\b','parámetros')
    if 'quotes' in en.lower():replace(r'\bcitas\b','cotizaciones')
    if 'computed' in en.lower():replace(r'\bcomputad[oa]s?\b',lambda m:m[0].lower().replace('computad','calculad'))
    if 'pricing' in en.lower():replace(r'fijación de precios','valoración')
    if 'figures' in en.lower():replace(r'\bcifras\b','figuras')
    if re.search(r'\bcall(?:s)?\b',en,re.I):
        replace(r'\bllamadas\b','calls');replace(r'\bllamada\b','call')
        replace(r'opciones? de calls?', 'opciones de compra')
        replace(r'calls? de opciones?', 'opciones de compra')
    if re.search(r'\bput(?:s)?\b',en,re.I):
        replace(r'\bpuestos\b','puts');replace(r'\bpuesto\b','put')
        replace(r'\bpuestas\b','puts');replace(r'\bpuesta\b','put')
    if re.search(r'\bstrike(?:s)?\b',en,re.I):
        replace(r'\bhuelgas\b','precios de ejercicio');replace(r'\bhuelga\b','precio de ejercicio')
        replace(r'precio de ejercicio pegajoso','strike constante')
    if re.search(r'\bstock(?:s)?\b',en,re.I):
        replace(r'\bexistencias\b','acciones');replace(r'\binventarios\b','acciones')
    if re.search(r'\bbonds?\b',en,re.I):
        replace(r'\bvínculos\b','bonos');replace(r'\bvínculo\b','bono')
        replace(r'\bobligaciones de cupón\b','bonos con cupón')
    if re.search(r'\bequit(?:y|ies)\b',en,re.I):
        replace(r'\bequidad(?:es)?\b','renta variable')
        replace(r'modelo de factor de renta variable','modelo de factores de renta variable')
    if 'momentum' in en.lower():replace(r'\bimpulso\b','momentum')
    if 'training' in en.lower():
        replace(r'\bcapacitación\b','entrenamiento')
        if 'formation' not in en.lower():replace(r'\bformación\b','entrenamiento')
    if 'variance' in en.lower():
        replace(r'\bvariación\b','varianza');replace(r'\bvariaciones\b','varianzas')
        replace(r'varianza integrada integrada','varianza integrada')
    if re.search(r'\bBlack\b',en):
        replace(r'\bNegro\b','Black');replace(r'\bNegra\b','Black')
    if 'ATM' in en:
        replace(r'(?:del |el )?cajero automático','ATM')
    if 'term structure' in en.lower() or 'term-structure' in en.lower():
        replace(r'estructuras? de término',lambda m:'estructuras temporales' if m[0].startswith('estructuras') else 'estructura temporal')
        replace(r'estructuras? a término',lambda m:'estructuras temporales' if m[0].startswith('estructuras') else 'estructura temporal')
    if 'forward' in en.lower():
        replace(r'\badelante\b','forward');replace(r'\bdelanter[oa]s?\b','forward')
    if 'cross-sectional' in en.lower():
        replace(r'sección cruzada','sección transversal')
        replace(r'secciones cruzadas','secciones transversales')
        replace(r'seccional cruzad[oa]','transversal')
    if 'risk-neutral' in en.lower():
        replace(r'probabilidad de que el riesgo sea neutro','probabilidad neutral al riesgo')
        replace(r'neutral de riesgo','neutral al riesgo')
        replace(r'neutro de riesgo','neutral al riesgo')
    if 'risk-free' in en.lower():replace(r'\bsin riesgo\b','libre de riesgo')
    if 'shortfall' in en.lower():
        replace(r'(?:déficit|faltante) esperado','pérdida esperada en cola')
        replace(r'escasez esperada','pérdida esperada en cola')
    if 'payoff' in en.lower():
        replace(r'\bretribuciones\b','pagos');replace(r'\bretribución\b','pago')
    if 'skewness' in en.lower():replace(r'\bsesgo\b','asimetría')
    if 'look-ahead' in en.lower():replace(r'mirada hacia adelante','anticipación de información')
    if 'holdout' in en.lower():
        replace(r'\bretención\b','muestra reservada')
        replace(r'\bretenciones\b','muestras reservadas')
    if 'withheld' in en.lower():replace(r'\bretenid[oa]s?\b','reservado')
    if 'turnover' in en.lower():replace(r'\bfacturación\b','rotación')
    replace(r'opciones estadounidenses','opciones americanas')
    replace(r'opción estadounidense','opción americana')
    replace(r'call europeo','call europea');replace(r'call americano','call americana')
    replace(r'calls europeos','calls europeas');replace(r'calls americanos','calls americanas')
    replace(r'put europeo','put europea');replace(r'put americano','put americana')
    replace(r'puts europeos','puts europeas');replace(r'puts americanos','puts americanas')
    return es
