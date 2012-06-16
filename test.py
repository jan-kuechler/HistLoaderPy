from HistLoader import *

hists = LoadHistogramsFromFile("test.txt")
print hists

hists["cosTheta"].FillRandom("gaus")
hists["cosTheta"].Draw()

hists["deltaPhi"][0].FillRandom("gaus")
hists["deltaPhi"][0].Draw()
