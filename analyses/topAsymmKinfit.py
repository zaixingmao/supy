#!/usr/bin/env python

import os,topAsymmShell,steps,calculables,samples,organizer,plotter,utils,math
import ROOT as r

class topAsymmKinfit(topAsymmShell.topAsymmShell) :
    def parameters(self) :
        pars = super(topAsymmKinfit,self).parameters()
        pars["effectiveLumi"] = 8000
        return pars

    def listOfCalculables(self,pars) :
        calcs = super(topAsymmKinfit,self).listOfCalculables(pars)
        calcs.append( calculables.Top.genTopSemiLeptonicWithinAcceptance( jetPtMin = 20, jetAbsEtaMax=3.5, lepPtMin=31, lepAbsEtaMax = 2.1))
        calcs.append( calculables.Top.genTopSemiLeptonicAccepted( pars['objects']['jet']))
        calcs.append( calculables.Top.genTopRecoIndex())
        return calcs

    def listOfSteps(self, pars) :
        obj = pars["objects"]
        lepton = obj[pars["lepton"]["name"]]
        lPtMin = pars["lepton"]["ptMin"]
        bVar = ("%s"+pars["bVar"]+"%s")%calculables.Jet.xcStrip(obj["jet"])
        
        return ([
            steps.Print.progressPrinter(),
            steps.Filter.pt("%sP4%s"%lepton, min = lPtMin, indices = "%sIndicesAnyIso%s"%lepton, index = 0),
            ]+topAsymmShell.topAsymmShell.cleanupSteps(pars)+[
            steps.Top.jetProbability(obj['jet'], "TrkCountingHighEffBJetTags", 100, -1, 15),
            ]+topAsymmShell.topAsymmShell.selectionSteps(pars, withPlots = False) +[
            #steps.Top.kinFitLook("fitTopRecoIndex"),
            steps.Filter.value("genTopSemiLeptonicWithinAcceptance", min = True),
            #steps.Histos.value("genTopWqqDeltaR",50,0,4),
            steps.Filter.value("genTopSemiLeptonicAccepted", min = True),
            #steps.Histos.value("genTopWqqDeltaR",50,0,4),
            ]+sum([[steps.Filter.label(tag),steps.Top.jetProbability(obj['jet'], tag,bins,min,max)] \
                          for tag,bins,min,max in [#("JetProbabilityBJetTags",100,-0.2,3),
                                                   #("JetBProbabilityBJetTags",100,-1,12),
                                                   #("CombinedSecondaryVertexBJetTags",100,-0.1,1),
                                                   #("CombinedSecondaryVertexMVABJetTags",100,-0.1,1),
                                                   #("TrkCountingHighEffBJetTags",100,-1,15)
                                                   ]],[]) + [
            #steps.Top.topProbLook(obj['jet']),
            steps.Other.assertNotYetCalculated("TopReconstruction"),
            steps.Filter.multiplicity("TopReconstruction",min=1),
            steps.Filter.value("genTopRecoIndex", min = 0),
            steps.Top.combinatorialBG(obj['jet']),
            #steps.Histos.value("genTopWqqDeltaR",50,0,4),
            #steps.Histos.value("fitTopWqqDeltaR",50,0,4),
            steps.Filter.label('selected combo'), steps.Top.kinFitLook("fitTopRecoIndex"), steps.Top.combinatoricsLook("fitTopRecoIndex"),
            steps.Filter.label('true combo'),  steps.Top.kinFitLook("genTopRecoIndex"), steps.Top.combinatoricsLook("genTopRecoIndex", jets = obj['jet']),
            steps.Filter.multiplicity("%sIndices%s"%obj["jet"], min=4, max=4),
            steps.Top.combinatorialBG(obj['jet']),
            steps.Top.combinatoricsLook("genTopRecoIndex", jets = obj['jet']),
            steps.Top.combinatoricsLook("fitTopRecoIndex"),
            ])
    
    def listOfSamples(self,pars) :
        from samples import specify
        return (specify(names = "tt_tauola_fj_mg", color = r.kRed,
                        #nFilesMax=1, nEventsMax=4100) +
                        effectiveLumi = pars["effectiveLumi"]) +
                specify(names = "tt_tauola_fj_mg", color = r.kBlue, weights = "wQQbar") +
                #specify(names = "tt_tauola_fj", color = r.kBlue,
                #        #nFilesMax=1, nEventsMax=4100)+
                #        effectiveLumi = pars["effectiveLumi"]) +
                #specify( names = "w_jets_mg", effectiveLumi = 100, color = 28 ) +
                [])

    def conclude(self,pars) :
        org = self.organizer(pars)
        org.scale(toPdf=True)
        
        pl = plotter.plotter(org,
                             psFileName = self.psFileName(org.tag),
                             doLog = False,
                             #noSci = True,
                             #pegMinimum = 0.1,
                             detailedCalculables = True,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             ).plotAll()

