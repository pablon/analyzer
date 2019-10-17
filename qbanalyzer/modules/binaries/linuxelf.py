__G__ = "(G)bd249ce4"

from ...logger.logger import logstring,verbose,verbose_flag
from ...mics.qprogressbar import progressbar
from ...mics.funcs import getentropy,getwords
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.descriptions import describe_reloc_type
from elftools.elf.descriptions import describe_symbol_type
from hashlib import md5
from elftools.elf.sections import SymbolTableSection

class LinuxELF:
    @verbose(verbose_flag)
    @progressbar(True,"Starting LinuxELF")
    def __init__(self,qbs):
        self.qbs = qbs

    @verbose(verbose_flag)
    def getrelocations(self,elf):
        _dict = []
        for section in elf.iter_sections():
            if isinstance(section, RelocationSection):
                symboltable = elf.get_section(section['sh_link'])
                for relocation in section.iter_relocations():
                    symbol = symboltable.get_symbol(relocation['r_info_sym'])
                    #address = hex(relocation['r_offset']) section['sh_flags']  section['sh_type']
                    #some have no names, need to check this out
                    if symbol.name != "":
                        _dict.append({  "Section":section.name,
                                        "Name":symbol.name,
                                        "Description":""})
        return _dict

    @verbose(verbose_flag)
    def getsymbols(self,elf):
        _dict = []
        for section in elf.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue
            for symbol in section.iter_symbols():
                if len(symbol.name) > 0:
                    _dict.append({  "Type":describe_symbol_type(symbol['st_info']['type']),
                                    "Symbol":symbol.name,
                                    "Description":""})
            return _dict

    @verbose(verbose_flag)
    def getdynamic(self,elf):
        _dict = []
        section = elf.get_section_by_name('.dynamic')
        if section != None:
            for tag in section.iter_tags():
                if tag.entry.d_tag != "DT_NEEDED":
                    continue
                _dict.append({  "Needed":tag.needed,
                                "Description":""})
        return _dict

    @verbose(verbose_flag)
    def getiter(self,elf):
        for segment in elf.iter_segments():
            if segment['p_type'] == 'PT_INTERP':
                return segment.get_interp_name()

    @verbose(verbose_flag)
    def getsection(self,elf):
        _dict = []
        for section in elf.iter_sections():
            if section.name != "":
                _dict.append({  "Section":section.name,
                                "MD5":md5(section.data()).hexdigest(),
                                "Entropy":getentropy(section.data()),
                                "Description":""})
        return _dict

    @verbose(verbose_flag)
    def checkelfsig(self,data):
        if  data["Details"]["Properties"]["mime"] == "application/x-pie-executable" or \
            data["Details"]["Properties"]["mime"] == "application/x-sharedlib" or \
            data["Details"]["Properties"]["mime"] == "application/x-executable":
            return True

    @verbose(verbose_flag)
    @progressbar(True,"Analyzing elf file")
    def getelfdeatils(self,data):
        with open(data["Location"]["File"], 'rb') as f, open(data["Location"]["File"], 'rb') as ff:
            data["ELF"] = { "General":{},
                            "Sections":[],
                            "Dynamic":[],
                            "Symbols":[],
                            "Relocations":[],
                            "_General":{},
                            "_Sections":["Section","MD5","Entropy","Description"],
                            "_Dynamic":["Needed","Description"],
                            "_Symbols":["Type","Symbol","Description"],
                            "_Relocations":["Section","Name","Description"]}
            elf = ELFFile(f)
            d = ff.read()
            _ep = hex(elf.header.e_entry)
            elf_machine = elf.header.e_machine
            elf_type = elf.header.e_type
            entropy = getentropy(d)
            sections = self.getsection(elf)
            relocations = self.getrelocations(elf)
            dynamic = self.getdynamic(elf)
            symbols = self.getsymbols(elf)
            interpreter = self.getiter(elf)
            data["ELF"]["General"] = {  "ELF Type" : elf_type,
                                        "ELF Machine" : elf_machine,
                                        "Entropy": entropy,
                                        "Entrypoint": _ep,
                                        "Interpreter":interpreter}
            data["ELF"]["Sections"] = sections
            data["ELF"]["Dynamic"] = dynamic
            data["ELF"]["Symbols"] = symbols
            data["ELF"]["Relocations"] = relocations
            self.qbs.adddescription("ManHelp",data["ELF"]["Symbols"],"Symbol")
            self.qbs.adddescription("LinuxSections",data["ELF"]["Sections"],"Section")
            words,wordsstripped = getwords(data["Location"]["File"])
            data["StringsRAW"] = {"words":words,
                                  "wordsstripped":wordsstripped}
