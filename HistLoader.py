from ROOT import *

def _startHist(line):
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
		
	#print "loaded list:", vals	
	return vals

def _addDef(hist, line):
	if line.find(":") != -1:
		parts = line.split(":")
		hist[parts[0].strip()] = _loadValue(parts[1].strip())
	else:
		hist[line] = True

def _gatherTemplates(hists):
	tpls = {}
	for n, d in hists.iteritems():
		if "*is-template*" in d:
			tpls[n] = d
	return tpls

def _resolve(tpls, d):
	if not "*inherits*" in d:
		return
		
	for parent in d["*inherits*"]:
		if not parent in tpls:
			print "Error: Could not find template " + parent
			return

		t = tpls[parent]
		for k, v in t.iteritems():
			if not k.startswith("*") and not k in d:
				d[k] = v
	
	del d["*inherits*"]

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
			_addDef(curHist, line.strip())
		else:
			if curHist:
				hists[curHist["name"]] = curHist
			curHist = _startHist(line.strip())
			
	hists[curHist["name"]] = curHist	
			
	return _resolveTemplates(hists)

def _checkTH1F(d):
	if not "nbins" in d:
		return False, "'nbins' missing"
	if not "min" in d:
		return False, "'min' missing"
	if not "max" in d:
		return False, "'max' missing"
	return True, None

def _loadTH1F(d):
	ok, msg = _checkTH1F(d)
	if not ok:
		print "Error in histogram '" + d["name"] + ": " + msg
		return None
	
	title = d["title"] if "title" in d else d["name"]

	hist = TH1F(d["name"], title, int(d["nbins"]), float(d["min"]), float(d["max"]))
	
	if "xtitle" in d:
		hist.GetXaxis().SetTitle(d["xtitle"])
	if "ytitle" in d:
		hist.GetYaxis().SetTitle(d["ytitle"])		
	
	return hist
	
_loaders = {
	"TH1F": _loadTH1F
}

def _handleVariables(d, i):
	result = d.copy()

	for key, val in d.iteritems():
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
			
			print name
			
			var = None
			if name in d:
				if type(d[name]) is list:
					var = d[name][i]
				else:
					var = d[name]
			
			if name and var:
				print name, var
				result[key] = result[key].replace(name, var)
			
			pos = val.find("$", end)
	
	#print result
	return result

def _handleRange(d):
	if not "*is-range*" in d:
		return d
	
	count = d["*count*"]
	res = []
	for i in range(count):
		x = d.copy()
		x["name"] += str(i)
		res.append(_handleVariables(x, i))
	
	return res

def LoadHist(d):
	type = "TH1F"
	if "type" in d:
		type = d["type"]
		
	if not type in _loaders:
		print "Error: Unknown histogram type " + type
		
	if "*is-range*" in d:
		ds = _handleRange(d)
		hists = []
		for x in ds:
			hists.append(_loaders[type](x))
		return hists
	else:
		d = _handleVariables(d, 0)
		return _loaders[type](d)

def LoadHistogramsFromFile(fileName):
	hists = _loadDefinitions(fileName)
	
	loaded = {}
	for n, d in hists.iteritems():
		if not "*is-template*" in d:
			loaded[n] = LoadHist(d)
	
	return loaded

