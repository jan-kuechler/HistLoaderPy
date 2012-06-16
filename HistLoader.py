from ROOT import *

def _handleFirstLine(line):
	h = {}
	if line.startswith("template "):
		h["*is-template*"] = True
		line = line[9:].strip()
	elif line.startswith("range("):
		h["*is-range*"] = True
		end = line.find(")")
		count = line[6:end]
		h["*count*"] = int(count)
		line = line[end+1:].strip()
	
	if line.find(":") != -1:
		parts = line.split(":")
		h["name"] = parts[0].strip()
		
		parents = parts[1].strip()
		if parents.find(",") == -1:	
			h["*inherits*"] = [parents]
		else:
			h["*inherits*"] = []
			for p in parents.split(","):
				h["*inherits*"].append(p.strip())
	else:
		h["name"] = line
	
	return h

def _loadValue(val):
	if not (val.startswith("[") and val.endswith("]")):
		return val
	
	vals = []
	for v in val[1:-1].split(";"):
		vals.append(v.strip())
		
	return vals

def _handleTabLine(hist, line):
	if line.find(":") != -1:
		parts = line.split(":")
		hist[parts[0].strip()] = _loadValue(parts[1].strip())
	else:
		hist[line] = True

def _gatherTemplates(hists):
	tpls = {}
	for n, defs in hists.iteritems():
		if "*is-template*" in defs:
			tpls[n] = defs
	return tpls

def _resolve(tpls, defs):
	if not "*inherits*" in defs:
		return
		
	for parent in defs["*inherits*"]:
		if not parent in tpls:
			print "Error: Could not find template " + parent
			return

		t = tpls[parent]
		for k, v in t.iteritems():
			if not k.startswith("*") and not k in defs:
				defs[k] = v
	
	del defs["*inherits*"]

def _resolveTemplates(hists):
	tpls = _gatherTemplates(hists)
	
	for n, d in hists.iteritems():
		_resolve(tpls, d)
	
	return hists
	
def _loadDefinitions(fileName):
	f = open(fileName, 'r')
	
	hists = {}
	curHist = None
	
	ln = 0
	for line in f.readlines():
		ln = ln + 1
		if line.strip() == "" or line.strip().startswith("#"):
			continue
			
		if line[0:1] == "\t":
			if curHist == None:
				return False, "Syntax error in line " + str(ln)
			_handleTabLine(curHist, line.strip())
		else:
			if curHist:
				hists[curHist["name"]] = curHist
			curHist = _handleFirstLine(line.strip())
			
	hists[curHist["name"]] = curHist	
			
	return _resolveTemplates(hists)
	
def _binWidthToNBins(binwidth, min, max):
	return math.floor(abs(max - min) / binwidth)
	
def _checkAxis(defs, axis):
	min = "min" + axis
	max = "max" + axis
	nbins = "nbins" + axis
	binwidth = "binwidth" + axis
	
	if not min in defs:
		return False, "'" + min + "' missing"
	if not max in defs:
		return False, "'" + max + "' missing"
		
	if not nbins in defs:
		if binwidth in defs:
			defs[nbins] = _binWidthToNBins(defs[binwidth], defs[min], defs[max])
		else:
			return False, "'" + nbins + "' missing"
		
	return True, None

def _loadTH1F(defs):
	ok, msg = _checkAxis(defs, "")
	if not ok:
		print "Error in histogram '" + defs["name"] + ": " + msg
		return None
	
	title = defs["title"] if "title" in defs else defs["name"]

	hist = TH1F(defs["name"], title, int(defs["nbins"]), float(defs["min"]), float(defs["max"]))
	
	if "xtitle" in defs:
		hist.GetXaxis().SetTitle(defs["xtitle"])
	if "ytitle" in defs:
		hist.GetYaxis().SetTitle(defs["ytitle"])		
	
	return hist
	
_loaders = {
	"TH1F": _loadTH1F
}

def _handleVariables(defs, i):
	result = defs.copy()

	for key, val in defs.iteritems():
		if not type(val) is str:
			continue

		# replace all occurences of $name with their values
		start = 0
		pos = val.find("$")
		while pos != -1:
			end = val.find(" ", pos)
			name = None
			if end == -1:
				name = val[pos:]
			else:
				name = val[pos:end]
			
			var = None
			if name in defs:
				if type(defs[name]) is list:
					var = defs[name][i]
				else:
					var = defs[name]
			else:
				print "No " + name
			
			if name and (var != None):
				result[key] = result[key].replace(name, var)
			
			pos = val.find("$", end)
	
	return result

def _handleRange(defs):
	if not "*is-range*" in defs:
		return defs
	
	count = defs["*count*"]
	res = []
	for i in range(count):
		x = defs.copy()
		x["name"] += str(i)
		res.append(_handleVariables(x, i))
	
	return res

def LoadHist(defs):
	type = "TH1F"
	if "type" in defs:
		type = defs["type"]
		
	if not type in _loaders:
		print "Error: Unknown histogram type " + type
		
	if "*is-range*" in defs:
		defrange = _handleRange(defs)
		hists = []
		for d in defrange:
			hists.append(_loaders[type](d))
		return hists
	else:
		defs = _handleVariables(defs, 0)
		return _loaders[type](defs)

def LoadHistogramsFromFile(fileName):
	hists = _loadDefinitions(fileName)
	
	loaded = {}
	for n, d in hists.iteritems():
		if not "*is-template*" in d:
			loaded[n] = LoadHist(d)
	
	return loaded
