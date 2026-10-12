from pathlib import Path
ROOT=Path(__file__).parent
notebook=(ROOT/'notebook.js').read_text(encoding='utf-8')
notebook=notebook.replace("x:'Synthetic month',y:","x:'Synthetic month',snap:true,y:").replace("x:'Signal decile',y:","x:'Signal decile',snap:true,y:")
(ROOT/'notebook.js').write_text(notebook,encoding='utf-8')
s=(ROOT.parent/'yield-curve-modelling'/'notebook.js').read_text(encoding='utf-8')
draw=s[s.index('function draw(host,panels,title){'):s.index('function audit(p,model){')]
draw=draw.replace("mode:'line'","mode:panel.snap?'snap':'line'")
(ROOT/'draw.js').write_text("(() => {\nconst colors=['#a7bdb3','#d3ad84','#91a9bd','#7e8d86'];\n"+draw+"\nwindow.FactorPlots={draw};\n})();",encoding='utf-8')
