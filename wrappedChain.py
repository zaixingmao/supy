import copy,array
import ROOT as r
from collections import defaultdict

class wrappedChain(dict) : 

    def __init__(self, chain, calculables = [], useSetBranchAddress = True, leavesToBlackList = [], preferredCalcs = []) :
        """Set up the nodes"""
        self.__activeNodes = defaultdict(int)
        self.__activeNodeList = []
        self.__chain = chain

        if (not chain) or chain.GetEntry(0)==0 : return
        for branch in chain.GetListOfBranches() :
            nameB = branch.GetName()
            nameL = (lambda nL: nameB if nL=="_" else nL )(branch.GetListOfLeaves().At(0).GetName())
            if nameL in leavesToBlackList : continue
            dict.__setitem__(self, nameL, self.__branchNode( nameL, nameB, chain, useSetBranchAddress) )

        names = [c.name() for c in calculables]
        if len(names)!=len(set(names)) :
            for name in names :
                assert names.count(name)==1,"Duplicate calculable name: %s"%name

        for calc in calculables :
            name = calc.name()
            if name in self and name not in preferredCalcs : continue
            dict.__setitem__(self, name, copy.deepcopy(calc) )
            dict.__getitem__(self, name).source = self
            dict.__getitem__(self, name).updated = False

    def activeKeys(self) : return self.__activeNodes.keys()
    def activeKeyTypes(self) : return [str(type(self.__activeNodes[key].value)).split("'")[1].replace("wrappedChain.","") for key in self.__activeNodes.keys()]

    def entries(self, nEntries = -1 ) :
        """Generate the access dictionary (self) for each entry in TTree."""
        if not self.__chain: return
        chain = self.__chain
        nEntries = (lambda x,y : min(x,y) if x>=0 else y)( nEntries, chain.GetEntries() ) 
        iTreeFirstEntry = 0
        
        for nTree in range(chain.GetNtrees()) :
            chain.LoadTree(iTreeFirstEntry)
            for node in self.__activeNodeList : node.setAddress() 
            tree = chain.GetTree()
            if not tree : continue
            nTreeEntries = tree.GetEntries()

            for iTreeEntry in range( nTreeEntries )  :
                self.entry = iTreeFirstEntry + iTreeEntry
                if nEntries <= self.entry : self.entry-=1; return
                self.__localEntry = iTreeEntry
                for node in self.__activeNodeList : node.updated = False
                yield self
            iTreeFirstEntry += nTreeEntries

    def __getitem__(self,key) :
        """Access the value of the branch or calculable specified by 'key' for the current entry"""
        node = self.__activeNodes[key]
        if not node :
            node = dict.__getitem__(self,key)
            self.__activeNodes[key] = node
            self.__activeNodeList.append(node)
            node.setAddress()
            node.updated = True
            node.update(self.__localEntry)
        elif not node.updated :
            node.updated = True
            node.update(self.__localEntry)
        return node.value

    def __setitem__(self,key,value) :
        raise Exception("wrappedChain entries are read-only.")


    class __branchNode(object) :
        """Internal wrapper for branch nodes."""
        def __init__(self, nameL, nameB, chain, useSetBranchAddress) :
            def className(nameL, nameB, chain) :
                return chain.GetBranch(nameB).GetLeaf(nameL).Class().GetName()

            def address(nameL, nameB, chain, useSetBranchAddress) :
                if not useSetBranchAddress : return None
                leaf = getattr(chain, nameL)

                if type(leaf)==int or type(leaf)==long : return array.array('l',[0])
                elif type(leaf)==float :
                    leafClassName = className(nameL, nameB, chain)
                    if leafClassName=="TLeafF" : return array.array('f',[0.0])
                    if leafClassName=="TLeafD" : return array.array('d',[0.0])
                    assert False,"leaf %s %s %s %s is not supported"%(nameB, nameL, str(type(leaf)), leafClassName)
                elif str(type(leaf))=="<type 'ROOT.PyUIntBuffer'>"   : return array.array('i',[0]*256)
                elif str(type(leaf))=="<type 'ROOT.PyDoubleBuffer'>" : return array.array('d',[0]*256)
                elif str(type(leaf))=="<type 'ROOT.PyFloatBuffer'>"  : return array.array('f',[0]*256)
                else :
                    self.value = copy.deepcopy(leaf)
                    return r.AddressOf(self.value)

            self.value = None
            self.updated = False
            self.nameL = nameL
            self.nameB = nameB
            self.chain = chain
            self.branch = None
            self.address = address(nameL, nameB, chain, useSetBranchAddress)
            self.valIsArrayZero = type(self.address) == array.array and len(self.address) == 1
            if type(self.address) == array.array and len(self.address)>1 :
                self.value = self.address

        def setAddress(self) :
            self.branch = self.chain.GetBranch(self.nameB)
            if self.address : self.branch.SetAddress( self.address )
            
        def update(self,localEntry) :
            self.branch.GetEntry(localEntry)
            if      not self.address : self.value = getattr(self.chain, self.nameL)
            elif self.valIsArrayZero : self.value = self.address[0]
                
    class calculable(object) :
        """Inherit wrappedChain.calculable and define update(self,localEntry) for a calculable node"""

        def update(self,localEntry) :
            """Set self.value according to dictionary self.source.

            You can safely ignore localEntry.
            You can override the name function.
            """
            raise Exception("Not Implemented!")

        def name(self) :
            if not hasattr(self,"fixes") : self.fixes = ("","")
            return self.fixes[0] + self.__class__.__name__ + self.fixes[1]

        def setAddress(self) :
            pass

        def stash(self,leafNames, fixes=None) :
            Name = self.name()
            for leaf in leafNames:
                assert not hasattr(self,leaf), "%s already has attribute %s"%(Name,leaf)
                setattr(self,leaf,("%s"+leaf+"%s")%(fixes if fixes else self.fixes))
