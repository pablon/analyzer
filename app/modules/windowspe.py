__G__ = "(G)bd249ce4"

from ..logger.logger import logstring,verbose,verbose_flag,verbose_timeout
from ..mics.funcs import getwords,getentropy,getentropyfloatret
from ..intell.qbdescription import adddescription
from pefile import PE,RESOURCE_TYPE,DIRECTORY_ENTRY
from hashlib import md5
from magic import from_file
from datetime import datetime
from M2Crypto import BIO, m2, SMIME, X509

class WindowsPe:
    @verbose(True,verbose_flag,verbose_timeout,"Starting WindowsPe")
    def __init__(self):
        pass

    @verbose(True,verbose_flag,verbose_timeout,None)
    def whattype(self,pe) -> str:
        '''
        check file exe or dll or driver
        '''
        if pe.is_exe():
            return "exe"
        elif pe.is_dll():
            return "dll"
        elif pe.is_driver():
            return "driver"

    @verbose(True,verbose_flag,verbose_timeout,None)
    def checkifsinged(self,pe) -> list:
        '''
        check file if it has Signature or not
        '''
        i = 0
        _list = []
        _extracted = {}
        Problems = False 
        address = pe.OPTIONAL_HEADER.DATA_DIRECTORY[DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_SECURITY']].VirtualAddress
        if address != 0:
            try:
                sig = pe.write()[address+8:]
                m2cbio = BIO.MemoryBuffer(bytes(sig))
                if m2cbio:
                    pkcs7bio = m2.pkcs7_read_bio_der(m2cbio.bio_ptr())
                    if pkcs7bio:
                        pkcs7 = SMIME.PKCS7(pkcs7bio)
                        for cert in pkcs7.get0_signers(X509.X509_Stack()):
                            tempcert = "CERT_{}".format(i)
                            _extracted[tempcert] = { "CommonName":None,
                                                     "OrganizationalUnit":None,
                                                     "Organization":None,
                                                     "Locality":None,
                                                     "StateOrProvinceName":None,
                                                     "CountryName":None,
                                                     "Start":None,
                                                     "Ends":None,
                                                     "SerialNumber":None}
                            try:
                                _extracted[tempcert]["CommonName"] = cert.get_subject().CN
                            except:
                                pass
                            try:
                                _extracted[tempcert]["OrganizationalUnit"] = cert.get_subject().OU
                            except:
                                pass
                            try:
                                _extracted[tempcert]["Organization"] = cert.get_subject().O
                            except:
                                pass
                            try:
                                _extracted[tempcert]["Locality"] = cert.get_subject().L
                            except:
                                pass
                            try:
                                _extracted[tempcert]["StateOrProvinceName"] = cert.get_subject().S
                            except:
                                pass
                            try:
                                _extracted[tempcert]["CountryName"] = cert.get_subject().C
                            except:
                                pass
                            try:
                                _extracted[tempcert]["Email"] = cert.get_subject().Email
                            except:
                                pass
                            try:
                                _extracted[tempcert]["Start"] = str(cert.get_not_before())
                            except:
                                pass
                            try:
                                _extracted[tempcert]["Ends"] = str(cert.get_not_after())
                            except:
                                pass
                            try:
                                _extracted[tempcert]["SerialNumber"] = cert.get_serial_number()
                                _extracted[tempcert]["SerialNumberMD5"] = cert.get_fingerprint('md5').lower().rjust(32, '0')
                            except:
                                pass
            except:
                Problems = True
            sighex = "".join("{:02x}".format(x) for x in sig)
            _list.append({"Wrong":Problems,
                          "SignatureHex":sighex})
        return _list,_extracted

    @verbose(True,verbose_flag,verbose_timeout,None)
    def findentrypointfunction(self,pe, rva) -> str:
        '''
        find entery point in sections
        '''
        for section in pe.sections:
            if section.contains_rva(rva):
                return section

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getdlls(self,pe) -> list:
        '''
        get dlls
        '''
        _list = []
        for dll in pe.DIRECTORY_ENTRY_IMPORT:
            if dll.dll.decode("utf-8",errors="ignore") not in str(_list):
                _list.append({"Dll":dll.dll.decode("utf-8",errors="ignore"),
                              "Description":""})
        return _list

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getsections(self,pe) -> list:
        '''
        get sections
        '''
        _list = []
        for section in pe.sections:
            sus = "No"
            entropy = getentropyfloatret(section.get_data())
            if entropy > 6 or entropy >= 0 and entropy <=1:
                sus = "True, {}".format(entropy)
            elif section.SizeOfRawData == 0:
                sus = "True, section size 0"
            _list.append({  "Section":section.Name.decode("utf-8",errors="ignore").strip("\00"),
                            "Suspicious":sus,
                            "Size":section.SizeOfRawData,
                            "MD5":section.get_hash_md5(),
                            "Entropy":getentropy(section.get_data()),
                            "Description":""})
        return _list

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getimportedfunctions(self,pe) -> list:
        '''
        get import functions
        '''
        _list = []
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                for func in entry.imports:
                    #print({entry.dll.decode("utf-8",errors="ignore"):func.name.decode("utf-8",errors="ignore")})
                    _list.append({ "Dll":entry.dll.decode("utf-8",errors="ignore"),
                                                "Function":func.name.decode("utf-8",errors="ignore"),
                                                "Description":""})
        return _list

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getexportedfunctions(self,pe) -> list:
        '''
        get export functions
        '''
        _list = []
        if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
            for func in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                _list.append({ "Function":func.name.decode("utf-8",errors="ignore"),
                                           "Description":""})
        return _list

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getrecourse(self,pe) -> (list,str):
        '''
        get resources
        '''
        manifest = ""
        _list = []
        _icons = []
        if hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                if resource_type.name is not None:
                    name = resource_type.name
                else:
                    name = RESOURCE_TYPE.get(resource_type.struct.Id)
                if name == None:
                    name = resource_type.struct.Id
                if hasattr(resource_type, "directory"):
                    for resource_id in resource_type.directory.entries:
                        if hasattr(resource_id, "directory"):
                            for resource_lang in resource_id.directory.entries:
                                resourcedata = pe.get_data(resource_lang.data.struct.OffsetToData, resource_lang.data.struct.Size)
                                if name == "RT_MANIFEST":
                                    try:
                                        manifest = resourcedata.decode("utf-8",errors="ignore")
                                    except:
                                        pass
                                sig = ""
                                if len(resourcedata) >= 12:
                                    sig = "".join("{:02x}".format(x) for x in resourcedata[:12])
                                _list.append({  "Resource":name,
                                                    "Offset":hex(resource_lang.data.struct.OffsetToData),
                                                    "MD5":md5(resourcedata).hexdigest(),
                                                    "Sig":sig,
                                                    "Description":""})
                                if name == "RT_ICON":
                                    _icons.append(resourcedata)
        return _list,manifest,_icons

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getstringfileinfo(self,pe) -> dict:
        _dict  = {}
        pe.parse_data_directories(directories=[DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        for fileinfo in pe.FileInfo[0]:
            if fileinfo.Key.decode() == 'StringFileInfo':
                for st in fileinfo.StringTable:
                    for entry in st.entries.items():
                        _dict.update({(entry[0].decode("utf-8",errors="ignore")):entry[1].decode("utf-8",errors="ignore")})
                if len(_dict) > 0:
                    return _dict
        return _dict

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getCharacteristics(self,pe) -> dict:
        '''
        get characteristics of file
        '''
        x = {"High Entropy":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA,
             "aslr":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE,
             "Force Integrity":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY,
             "dep":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_NX_COMPAT,
             "seh":not pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_NO_SEH,
             "No Bind":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_NO_BIND,
             "cfg":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_GUARD_CF,
             "No Isolation":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_NO_ISOLATION,
             "App Container":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_APPCONTAINER,
             "wdm Driver":pe.OPTIONAL_HEADER.IMAGE_DLLCHARACTERISTICS_WDM_DRIVER}
        return x

    @verbose(True,verbose_flag,verbose_timeout,None)
    def getdebug(self,pe) -> list:
        '''
        get debug directory 
        '''
        _list = []
        if hasattr(pe, "DIRECTORY_ENTRY_DEBUG"):
            for i in pe.DIRECTORY_ENTRY_DEBUG:
                _list.append({  "Name":i.entries.PdbFileName,
                                "Description":""})
        return _list

    @verbose(True,verbose_flag,verbose_timeout,None)
    def checkpesig(self,data) -> bool:
        '''
        check mime is exe or msi
        '''
        if  data["Details"]["Properties"]["mime"] == "application/x-dosexec" or \
            data["Details"]["Properties"]["mime"] == "application/x-msi":
            return True

    @verbose(True,verbose_flag,verbose_timeout,"Analyzing PE file")
    def getpedeatils(self,data):
        '''
        start analyzing exe logic, add descriptions and get words and wordsstripped from the file 
        '''
        data["PE"] = {  "General" : {},
                        "Characteristics":{},
                        "Singed":[],
                        "SignatureExtracted":{},
                        "Stringfileinfo":{},
                        "Sections":[],
                        "Dlls":[],
                        "Resources":[],
                        "Imported functions":[],
                        "Exported functions":[],
                        "Debug":[],
                        "Manifest":"",
                        "_General": {},
                        "_Characteristics": {},
                        "_Singed":["Wrong","SignatureHex"],
                        "__SignatureExtracted":{},
                        "_Stringfileinfo":{},
                        "_Sections":["Section","Suspicious","Size","Entropy","MD5","Description"],
                        "_Dlls":["Dll","Description"],
                        "_Resources":["Resource","Offset","MD5","Sig","Description"],
                        "_Imported functions":["Dll","Function","Description"],
                        "_Exported functions":["Dll","Function","Description"],
                        "_Debug":["Name","Description"],
                        "_Manifest":""}
        data["ICONS"] = {"ICONS":[]}
        pe = PE(data["Location"]["File"])
        ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        section = self.findentrypointfunction(pe,ep)
        sig = section.get_data(ep, 12)
        singinhex = "".join("{:02x}".format(x) for x in sig)
        data["PE"]["General"] = {   "PE Type" : self.whattype(pe),
                                    "Entrypoint": pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                                    "Entrypoint Section":section.Name.decode("utf-8",errors="ignore").strip("\00"),
                                    "Header checksum": hex(pe.OPTIONAL_HEADER.CheckSum),
                                    "Verify checksum": hex(pe.generate_checksum()),
                                    "Match checksum":pe.verify_checksum(),
                                    "Sig":singinhex,
                                    "imphash":pe.get_imphash(),
                                    "warning":pe.get_warnings() if len(pe.get_warnings())> 0 else "None",
                                    "Timestamp":datetime.fromtimestamp(pe.FILE_HEADER.TimeDateStamp).strftime('%Y-%m-%d %H:%M:%S')}
        data["PE"]["Characteristics"] = self.getCharacteristics(pe)
        data["PE"]["Singed"],data["PE"]["SignatureExtracted"] = self.checkifsinged(pe)
        data["PE"]["Stringfileinfo"] = self.getstringfileinfo(pe)
        data["PE"]["Sections"] = self.getsections(pe)
        data["PE"]["Dlls"] = self.getdlls(pe)
        data["PE"]["Resources"],data["PE"]["Manifest"],data["ICONS"]["ICONS"] = self.getrecourse(pe)
        data["PE"]["Imported functions"] = self.getimportedfunctions(pe)
        data["PE"]["Exported functions"] = self.getexportedfunctions(pe)
        adddescription("WinApis",data["PE"]["Imported functions"],"Function")
        adddescription("ManHelp",data["PE"]["Imported functions"],"Function")
        adddescription("WinDlls",data["PE"]["Dlls"],"Dll")
        adddescription("WinSections",data["PE"]["Sections"],"Section")
        adddescription("WinResources",data["PE"]["Resources"],"Resource")
        getwords(data,data["Location"]["File"])
