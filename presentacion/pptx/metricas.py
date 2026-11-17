"""Anchos de glifo y pares de kerning (GPOS 'kern') para reproducir en PowerPoint el espaciado de XeTeX.

PowerPoint no aplica el kerning OpenType de IBM Plex Sans; aquí se calcula como lo hace HarfBuzz y el
generador lo escribe como espaciado de carácter (atributo spc) en el primer glifo de cada par."""
from fontTools.ttLib import TTFont


class Fuente:
    def __init__(self, ruta):
        f = TTFont(ruta)
        self.upm = f["head"].unitsPerEm
        self.cmap = f.getBestCmap()
        self.hmtx = f["hmtx"]
        self.lookups = []
        if "GPOS" in f:
            g = f["GPOS"].table
            indices = []
            for fr in g.FeatureList.FeatureRecord:
                if fr.FeatureTag == "kern":
                    for i in fr.Feature.LookupListIndex:
                        if i not in indices:
                            indices.append(i)
            for i in sorted(indices):
                lk = g.LookupList.Lookup[i]
                subs = []
                for st in lk.SubTable:
                    if lk.LookupType == 9:
                        st = st.ExtSubTable
                    subs.append(st)
                self.lookups.append(subs)
        self._cache = {}

    def glifo(self, ch):
        return self.cmap.get(ord(ch))

    def avance(self, ch):
        g = self.glifo(ch)
        return 0 if g is None else self.hmtx[g][0] * 1000 / self.upm

    def kern(self, a, b):
        clave = (a, b)
        if clave in self._cache:
            return self._cache[clave]
        g1, g2 = self.glifo(a), self.glifo(b)
        total = 0
        if g1 is not None and g2 is not None:
            for subs in self.lookups:
                for st in subs:
                    cov = st.Coverage.glyphs
                    if g1 not in cov:
                        continue
                    if st.Format == 1:
                        ps = st.PairSet[cov.index(g1)]
                        hecho = False
                        for pvr in ps.PairValueRecord:
                            if pvr.SecondGlyph == g2:
                                v = getattr(pvr.Value1, "XAdvance", 0) if pvr.Value1 else 0
                                total += v or 0
                                hecho = True
                                break
                        if hecho:
                            break
                    else:
                        c1 = st.ClassDef1.classDefs.get(g1, 0)
                        c2 = st.ClassDef2.classDefs.get(g2, 0)
                        rec = st.Class1Record[c1].Class2Record[c2]
                        v = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                        total += v or 0
                        break
        total = total * 1000 / self.upm
        self._cache[clave] = total
        return total
