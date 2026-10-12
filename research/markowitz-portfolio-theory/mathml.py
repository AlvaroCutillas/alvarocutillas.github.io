"""Small, strict TeX-to-presentation-MathML renderer for this document's notation."""
import re
from html import escape

SYMBOLS = dict(zip(
    'alpha beta gamma delta epsilon theta lambda mu nu pi rho sigma tau phi varphi omega Gamma Delta Theta Lambda Phi Sigma Omega'.split(),
    'α β γ δ ε θ λ μ ν π ρ σ τ φ φ ω Γ Δ Θ Λ Φ Σ Ω'.split()))
SYMBOLS.update({'partial':'∂','infty':'∞','times':'×','cdot':'·','le':'≤','leq':'≤','ge':'≥','geq':'≥','ne':'≠','approx':'≈','sim':'∼','to':'→','rightarrow':'→','Rightarrow':'⇒','Longrightarrow':'⇒','in':'∈','notin':'∉','sup':'sup','max':'max','min':'min','ln':'ln','log':'log','exp':'exp','sum':'∑','int':'∫','prod':'∏','mid':'|','vert':'|','ell':'ℓ','mathbbQ':'ℚ','ldots':'…','pm':'±'})
OPERATORS = set('partial infty times cdot le leq ge geq ne approx sim to rightarrow Rightarrow Longrightarrow in notin sum int prod mid vert'.split())
NORMAL = set('sup max min ln log exp'.split())
SYMBOLS.update({'lim':'lim','downarrow':'↓','psi':'ψ','eta':'η','Pi':'Π','varepsilon':'ε'})
NORMAL.add('lim')
OPERATORS.update(['ldots','pm','downarrow'])
SYMBOLS.update({'propto':'∝','cos':'cos','sin':'sin','lceil':'⌈','rceil':'⌉','lfloor':'⌊','rfloor':'⌋'})
OPERATORS.update(['propto','lceil','rceil','lfloor','rfloor'])
NORMAL.update(['cos','sin'])
SYMBOLS.update({'longrightarrow':'⟶','cdots':'⋯','star':'⋆'})
SYMBOLS.update({'kappa':'κ','langle':'⟨','rangle':'⟩'})
OPERATORS.update(['langle','rangle'])
OPERATORS.update(['longrightarrow','cdots','star'])
class Parser:
    def __init__(self, source):
        source=source.replace(r'\frac12',r'\frac{1}{2}')
        self.tokens = re.findall(r'\\text\{[^{}]*\}|\\[a-zA-Z]+|\\.|\d+(?:\.\d+)?|[^\s]',source)
        self.i=0
    def take(self):
        if self.i>=len(self.tokens): raise ValueError('Unexpected end of expression')
        t=self.tokens[self.i]; self.i+=1; return t
    def group(self):
        if self.i<len(self.tokens) and self.tokens[self.i]=='{':
            self.i+=1; result=self.row('}'); return result
        return self.atom()
    def row(self, end=None):
        parts=[]
        while self.i<len(self.tokens):
            if self.tokens[self.i]==end: self.i+=1; return '<mrow>'+''.join(parts)+'</mrow>'
            a=self.atom()
            if not a: continue
            sub=sup=None
            while self.i<len(self.tokens) and self.tokens[self.i] in ['_','^']:
                op=self.take(); b=self.group()
                if op=='_': sub=b
                else: sup=b
            if sub and sup: a='<msubsup>'+a+sub+sup+'</msubsup>'
            elif sub: a='<msub>'+a+sub+'</msub>'
            elif sup: a='<msup>'+a+sup+'</msup>'
            parts.append(a)
        if end: raise ValueError('Unclosed group')
        return '<mrow>'+''.join(parts)+'</mrow>'
    def atom(self):
        t=self.take()
        if t.startswith(r'\text{'): return '<mtext>'+escape(t[6:-1])+'</mtext>'
        if t=='{': return self.row('}')
        if t in ['}','^','_']: raise ValueError('Invalid token '+t)
        if t.startswith('\\'):
            c=t[1:]
            if c in ['left','right','displaystyle','limits']: return ''
            if c in [',',';',':','quad','qquad','!',' ']: return '<mspace width="'+('0.7em' if c in ['quad','qquad'] else '0.15em')+'"/>'
            if c in ['{','}','%','|']: return '<mo>'+escape('‖' if c=='|' else c)+'</mo>'
            if c in ['frac','dfrac','tfrac']: return '<mfrac>'+self.group()+self.group()+'</mfrac>'
            if c=='sqrt': return '<msqrt>'+self.group()+'</msqrt>'
            if c in ['hat','widehat','bar','overline','tilde','widetilde']:
                return '<mover accent="true">'+self.group()+'<mo>'+{'hat':'^','widehat':'^','bar':'¯','overline':'¯','tilde':'~','widetilde':'~'}[c]+'</mo></mover>'
            if c in ['text','mathrm','operatorname','mathbb','mathcal','mathbf','mathsf']:
                if self.take()!='{': raise ValueError('Expected group for '+c)
                tokens=[]
                while self.i<len(self.tokens) and self.tokens[self.i]!='}': tokens.append(self.take())
                if self.take()!='}': raise ValueError('Unclosed text')
                value=''.join(tokens)
                if c=='mathbb': value={'Q':'ℚ','P':'ℙ','E':'𝔼','R':'ℝ','1':'𝟙'}.get(value,value)
                tag='mtext' if c=='text' else 'mi'
                variant='script' if c=='mathcal' else ('bold' if c=='mathbf' else ('sans-serif' if c=='mathsf' else 'normal'))
                return '<'+tag+' mathvariant="'+variant+'">'+escape(value)+'</'+tag+'>'
            if c not in SYMBOLS: raise ValueError('Unsupported command \\'+c)
            tag='mo' if c in OPERATORS or c in NORMAL else 'mi'
            return '<'+tag+(' form="prefix"' if c in NORMAL else '')+'>'+SYMBOLS[c]+'</'+tag+'>'
        if re.fullmatch(r'\d+(?:\.\d+)?',t): return '<mn>'+t+'</mn>'
        if t.isalpha() or t in 'ℚℙ𝔼': return '<mi>'+escape(t)+'</mi>'
        return '<mo>'+escape({'-':'−'}.get(t,t))+'</mo>'

def math(source, display=False):
    try: body=Parser(source).row()
    except Exception as exc: raise ValueError(f'{source}: {exc}') from exc
    return '<math xmlns="http://www.w3.org/1998/Math/MathML" display="'+('block' if display else 'inline')+'"><semantics>'+body+'<annotation encoding="application/x-tex">'+escape(source)+'</annotation></semantics></math>'
