import eftscaling

loop = eftscaling.load('STXS_ggF-SMEFTatNLO-2jet-loop.json')
loop.zeroTerms([['cpg']], allow_subset_match=True)

tree = eftscaling.load('STXS_ggF-SMEFTatNLO-2jet-tree.json')

tree_loop = eftscaling.load('STXS_ggF-SMEFTatNLO-2jet-tree-loop.json')
tree_loop.zeroTerms([['cpg', 'cpg']])

loop.add(tree)
loop.add(tree_loop)
loop.printToScreen(relative=True)