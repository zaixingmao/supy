import os,math,array, ROOT as r
try:
    import numpy as np
except:
    pass

#####################################
def generateDictionaries(inList, dir = None) :
    wd = os.getcwd()
    r.gSystem.ChangeDirectory((dir if dir!=None else wd)+"/cpp")
    for item in inList : r.gInterpreter.GenerateDictionary(*item)
    r.gSystem.ChangeDirectory(wd)
#####################################
def compileSources(inList) :
    for sourceFile in inList :
        r.gROOT.LoadMacro(sourceFile+"+")
#####################################
lvClass = None
def LorentzV(*args) :
    global lvClass
    if lvClass is None : lvClass = r.Math.LorentzVector(r.Math.PtEtaPhiM4D('float'))
    return lvClass(*args)
#####################################
def delete(thing) :
    #free up memory (http://wlav.web.cern.ch/wlav/pyroot/memory.html)
    thing.IsA().Destructor(thing)
#####################################
def canvas(name) :
    c = r.TCanvas(name,name, 260*2, 200*2)
    c.SetTopMargin(0.0)
    c.SetBottomMargin(0.0)
    c.SetRightMargin(0.0)
    c.SetLeftMargin(0.0)
    return c
#####################################
def rHist(name,bins,edges,poissonErrors=False) :
    hist = r.TH1D(name,"",len(bins), np.array(edges,dtype='double'))
    for i,bin in enumerate(bins) : 
        hist.SetBinContent(i+1,bin)
        hist.SetBinError(i+1,math.sqrt(bin) if poissonErrors else 0)
    return hist
#####################################
def binValues(hist) : return [hist.GetBinContent(i) for i in range(0,hist.GetNbinsX()+2)]
#####################################
def tCanvasPrintPdf(canvas, fileName, verbose = True) :
    illegal = [':','[',']','(',')']
    for ill in illegal : fileName = fileName.replace(ill,"_")
    canvas.Print("%s.eps"%fileName)
    os.system("epstopdf %s.eps"%fileName)
    os.system("rm %s.eps"%fileName)
    if verbose : print "Output file: %s.pdf"%fileName
#####################################
def ratioHistogram( num, den, relErrMax=0.25) :

    def groupR(group) :
        N,D = [float(sum(hist.GetBinContent(i) for i in group)) for hist in [num,den]]
        return N/D if D else 0

    def groupErr(group) :
        N,D = [float(sum(hist.GetBinContent(i) for i in group)) for hist in [num,den]]
        ne2,de2 = [sum(hist.GetBinError(i)**2 for i in group) for hist in [num,den]]
        return math.sqrt( ne2/N**2 + de2/D**2 ) * N/D if N and D else 0

    def regroup(groups) :
        err,iG = max( (groupErr(g),groups.index(g)) for g in groups )
        if err < relErrMax or len(groups)<3 : return groups
        iH = max( [iG-1,iG+1], key = lambda i: groupErr(groups[i]) if 0<=i<len(groups) else -1 )
        iLo,iHi = sorted([iG,iH])
        return regroup(groups[:iLo] + [groups[iLo]+groups[iHi]] + groups[iHi+1:])

    groups = regroup( [(i,) for i in range(1,1+num.GetNbinsX())] )
    ratio = r.TH1D("ratio"+num.GetName()+den.GetName(),"",len(groups), array.array('d', [num.GetBinLowEdge(min(g)) for g in groups ] + [num.GetXaxis().GetBinUpEdge(num.GetNbinsX())]) )
    for i,g in enumerate(groups) :
        ratio.SetBinContent(i+1,groupR(g))
        ratio.SetBinError(i+1,groupErr(g))
    return ratio
#####################################
