from eftscaling import EFT2ObsHist, EFTScaling

loop = EFT2ObsHist.fromJSON('STXS_ggF-SMEFTatNLO-2jet-loop_raw.json')
loop.zeroTerms([['cpg']], allow_subset_match=True)

tree = EFT2ObsHist.fromJSON('STXS_ggF-SMEFTatNLO-2jet-tree_raw.json')

tree_loop = EFT2ObsHist.fromJSON('STXS_ggF-SMEFTatNLO-2jet-tree-loop_raw.json')
tree_loop.zeroTerms([['cpg', 'cpg']])

loop.add(tree)
loop.add(tree_loop)
loop.printToScreen(relative=True)

EFTScaling.fromEFT2ObsHist(loop).writeToJSON('STXS_ggF-SMEFTatNLO-2jet-merged.json')