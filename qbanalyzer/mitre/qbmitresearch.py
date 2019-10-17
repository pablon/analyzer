__G__ = "(G)bd249ce4"

from ..logger.logger import logstring,verbose,verbose_flag
from ..mics.qprogressbar import progressbar
from ..mics.funcs import iptolong
from nltk.corpus import words
from nltk.tokenize import word_tokenize
from json import loads
from os import mkdir, path

#this module need some optimization

verbose_flag = False

class QBMitresearch:
    @verbose(verbose_flag)
    @progressbar(True,"Starting QBMitresearch")
    def __init__(self,mitre):
        self.mitrepath = path.abspath(path.join(path.dirname( __file__ ),'mitrefiles'))
        if not self.mitrepath.endswith(path.sep): self.mitrepath = self.mitrepath+path.sep
        if not path.isdir(self.mitrepath): mkdir(self.mitrepath)
        self.mitre = mitre
        self.parsediocs = self.mitrepath+"parsediocs.json"

    @verbose(verbose_flag)
    def searchinmitreandreturn(self,s,attack):
        for x in s:
            if "id" in x and "attack-pattern" in x["id"]:
                if x['external_references'][0]['external_id'].lower() == attack:
                    return x
        return None

    @progressbar(True,"Check with attack patterns")
    @verbose(verbose_flag)
    def checkmitresimilarity(self,data):
        _list = []
        f = loads(open(self.parsediocs).read())
        for attack in f:
            for ioc in f[attack]:
                if ioc.lower() in self.wordsstripped:
                    _list.append(ioc.lower())
            if len(_list) > 0:
                x = self.searchinmitreandreturn(self.mitre.fulldict,attack)
                if x:
                    data["Attack"].append({ "Id":attack,
                                            "Name":x["name"],
                                            "Detected":','.join(_list),
                                            "Description":x["description"]})
                else:
                    data["Attack"].append({ "Id":attack,
                                            "Name":"None",
                                            "Detected":','.join(_list),
                                            "Description":"None"})
            _list = []

    @progressbar(True,"Check with mitre artifacts")
    @verbose(verbose_flag)
    def checkmitre(self,data):
        for word in self.words:
            _word = word.lower().decode("utf-8")
            toolrecords = self.mitre.findtool(_word)
            if toolrecords:
                for record in toolrecords:
                    data["Binary"].append({  "Word":_word,
                                            "Name":record["name"],
                                            "Description":record["description"]})
            malwarerecords = self.mitre.findmalware(_word)
            if malwarerecords:
                for record in malwarerecords:
                    data["Binary"].append({  "Word":_word,
                                            "Name":record["name"],
                                            "Description":record["description"]})
        return True

    @progressbar(True,"Check with mitre")
    @verbose(verbose_flag)
    def checkwithmitre(self,data):
        self.words = data["StringsRAW"]["words"]
        self.wordsstripped = data["StringsRAW"]["wordsstripped"]
        data["MITRE"] = {"Binary":[],
                         "Attack":[],
                         "_Binary":["Word","Name","Description"],
                         "_Attack":["Id","Name","Detected","Description"]}
        #engsorted = self.sortbylen(self.checkwithenglish()["English"])
        #unksorted = self.sortbylen(self.checkwithenglish()["UnKnown"])
        #b64 = self.checkbase64()
        self.checkmitre(data["MITRE"])
        self.checkmitresimilarity(data["MITRE"])