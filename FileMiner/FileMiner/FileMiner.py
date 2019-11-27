### FILE EXPLORER AND DIRECTORY IMPORTS ###

import os, sys, io, pathlib, fileinput, stat, filecmp, tempfile, glob, fnmatch, linecache, shutil

### TIME/TEXT/NUMBER/FILE/FOLDER MANIPULATION IMPORTS ###

import re
import time
import pandas
import pkgutil
import datetime
import subprocess
from fuzzywuzzy import fuzz
from datetime import datetime
from memory_profiler import LogFile as lgf
from memory_profiler import profile as prfe
import xlsxwriter, xlwings, xlparser, xlrd, xlutils, xlwt
import collections, itertools, functools, threading, socket, slugify

### PACKAGE IMPORTS ###

from Exceptions import *
from FileAux import *

#################################### FILE MINER CLASS OBJECT ####################################

'''
File Miner Class That Takes a target folder and renames specific
target text in file names

NEW FUNCTION CLASS AND METHOD IDEAS:
   - def Change_File_Type()
   - def Read_First_Line(File_Type = [.doc,.pdf])
   - class PyUtilities()
   
'''

class FileMiner(object):

    ''' Initialize Class Variables '''
    fos = "{}_profiler_{}.log".format('folder', len([x for x in os.listdir(os.getcwd()) if all(dl in x for dl in "{}_profiler_{}.log".split("{}"))])+1)
    fis = "{}_profiler_{}.log".format('file', len([x for x in os.listdir(os.getcwd()) if all(dl in x for dl in "{}_profiler_{}.log".split("{}"))])+1)
    osfields = 'mode ino dev nlink uid gid size atime mtime ctime blocks blksize rdev flags gen birthtime ftype attrs obtype'.split()
    
    def __init__(self, N_Dir = os.getcwd(), Collect_Explorer=False, Build_Dataframe = False, Load_Last_Export = False): 
        ''' Initialize Instance Variables '''
        self.N_Dir = N_Dir
        self.Collect_Explorer = Collect_Explorer
        self.Build_Dataframe = Build_Dataframe
        self.Load_Last_Export = Load_Last_Export

        ''' Other Variables and Custom Named Methods'''
        self._fz = fuzz
        self._pd = pandas
        self._dime = datetime
        self._dlst = os.listdir
        self.Modify = os.rename
        self.Delete = os.remove
        self._filopen = os.startfile
        self._folopen = subprocess.Popen
        self._strdate = datetime.strptime
        self._ppath = pathlib.PureWindowsPath
        self._ziplong = itertools.zip_longest
        self._msg = 'str "<Output Text>"'
        self.N_Dir = self.N_Dir.replace(self._ppath(self.N_Dir).root,"\\")
        self._chkfilnams = ["FileMinerData ", "FolderDataFrame ", "FileDataFrame ", "InfoDataFrame ", "FolderPaths ", "FilePaths "]
        
        ''' Data Containers '''
        self.Folder_List = []
        self.File_List = []
        self.Extension_List = []
        self.Error_List = []
        self.Folder_Data = []
        self.File_Data = []
        self.Extension_Data = []
        self.Folder_Data_Frame = []
        self.File_Data_Frame = []
        self.Info_Data_Frame = []
        self.Filetered_Folders = []
        self.Filtered_Files = []
        self.Modification_Matrix = {}
        self.Character_Removal_Targets = []
        self.Modification_Log = {}
        self.Saved_Data_Files = []
        
        if self.Build_Dataframe and not self.Collect_Explorer:
            raise SequenceError('Data must be compiled before Dataframe can be constructed. Set "Collect_Explorer" = True or "Build_Dataframe" = False and Run GetData() to generate')
        elif self.Collect_Explorer and self.Load_Last_Export:
            raise InvalidError('"Collect_Explorer" and "Load_Last_Export" can\'t be run in conjuction. Either run "Collect_Explorer" to build new file structure from root or load from saved files using "Load_Last_Export"')

        os.chdir(N_Dir)

        if self.Collect_Explorer:
            self._msg = self.GetData(Auto_Build = Build_Dataframe)
            print(self._msg)
            self._msg = 'str "<Output Text>"'
        elif self.Load_Last_Export:
            Flist = [tdt for tdt in [dfil.split(" ")[-1] for dfil in self._dlst(self.N_Dir) if any(cfn in dfil for cfn in self._chkfilnams)] if Vali_Date(tdt)]
            Tdate = max(Flist, key= lambda dt: strdate(dt, '%m-%d-%Y'))
            if Tdate:
                self._msg = self.GetData(Load_Data_Id = Tdate)
                print(self._msg)
                self._msg = 'str "<Output Text>"'
                
                
    def __str__(self):
        return "File and Folder Data Manipulator - "+os.getcwd()
              
    def __update_mod_matrix__(self, oval, nval):
        ''' Internal modification matrix maintainer '''

        curmod = len(self.Modification_Matrix)
        chktyp = lambda var1, var2 : (var1 if isinstance(var1,list) else [var1]) + (var2 if isinstance(var1,list) else [var2])
        
        if oval and nval:
            if type(oval) == str:
                self.Modification_Matrix[oval] =  chktyp(nval, self.Modification_Matrix[oval])
            elif type(oval) == dict:
                self.Modification_Matrix.update(oval)
            else:
                return "Please supply a 'Key' dictionary or a 'key' and 'Replacement' string or list to add to the Modification Matrix"
            
            return "Modification Matrix Updated"
        else:
            return "Please supply a 'Key' and 'Replacement' string or list to add to the Modification Matrix"
        pass

    def __update_char_tar__(self, chars, extn):
        ''' Internal Character Removal Set Maintainer '''
        
        chars = list(chars) if isinstance(chars,(list, tuple)) else [chars] if isinstance(chars,(str, float, int, bytes)) else [str(chars, 'utf-8')] if isinstance(chars,bytes) else None

        if extn != "":
            if self.Extension_List != []:
                if type(extn) != str or extn not in self.Extension_List:
                    raise InvalidError("Please provide an existing single file extension as a string to restrict removal if desired")
                chars = [[extn,char] for char in chars]
            else:
                raise EmptySetError("Please run the 'GetData()' function with desired file location to build data for modification")
        
        if chars:
            self.Character_Removal_Targets += chars
            return "Characters Added Successfully"
        else:
            raise InvalidError("Please enter as standard variable types [list, tuple, str, float, int, bytes] for removal characters")
        return None

    def __window_data_extract__(self, start, filstats, prntrecs):
        ''' Build dataset for initial evaluation '''
        
        StopWatch = time.time()
        Mp, extlst, fillst, follst, tlst, qlst, templst, errlst, mastlst = pathlib.Path, [], [], [], [], [], [], [], []
        
        ext_strip = lambda fils: [str(ex)[str(ex).index('.'):] for ex in fils if '.' in str(ex)]
        sub_fol_split = lambda ftar: [fo for fo in list(Mp(ftar).iterdir()) if Mp(fo).is_dir()]
        fil_fol_split = lambda ptar: [[fi for fi in list(Mp(ptar).iterdir()) if not Mp(fi).is_dir()],[fo for fo in list(Mp(ptar).iterdir()) if Mp(fo).is_dir()]]

        _, mastlst = fillst, follst = fil_fol_split(start)

        while follst:
            for fol in follst:
                try:
                    tlst, qlst = fil_fol_split(fol)
                    templst += qlst
                    fillst += tlst
                except (PermissionError,OSError):
                    errlst.append(fol)
            if prntrecs: print("Current Run at: %.2f Minutes"%int((time.time()-StopWatch)/60))
            mastlst += templst
            follst = templst
            templst = []

        if filstats == True:
            extlst = ext_strip(fillst)
            extlst_data, extlst = [(ext, extlst.count(ext)) for ext in list(set(extlst))], list(set(extlst)) 
            mastlst_data, fillst_data = [[(fol,os.stat(fol)) for fol in mastlst if os.path.exists(fol)], [(fil,os.stat(fil)) for fil in fillst if os.path.exists(fil)]]
            return [mastlst, fillst, extlst, errlst, mastlst_data, fillst_data, extlst_data]
        else:
            extlst = list(set(ext_strip(fillst)))
            return [mastlst, fillst, extlst, errlst]
        pass

    def __window_data_loader__(self, run_id):
        ''' Load data from previous run to be used as basis '''

        tarfil, tarsht, dirlst, retlst = self._chkfilnams, ['FolderPaths', 'FolderData', 'FilePaths', 'FileData', 'Extensions'], self._dlst(self.N_Dir), []

        for fil in dirlst:
            if run_id in fil:
                tname = [sfil in fil for sfil in tarfil]
                if len(tname) == 1:
                    tname = tname[0]
                    if ".xls" in fil:
                        if tname not in [n for n,f in retlst]:
                            fil = self._pd.ExcelFile(fil)
                            for sht in fil.sheet_names:
                                if sht in tarsht:
                                    subfil = fil.parse(sht).values
                                    tname = sht.replace('ns','n') + " "
                                    retlst.append([tname, subfil])
                    elif ".pickle" in fil:
                        retlst.append([tname, self._pd.read_pickle(fil)])
                    elif ".txt" in fil:
                        if tname not in [n for n,f in retlst]:
                            fpaths = []
                            tfil = open(fil, 'r+')
                            fil = tfil.read().split('\n')
                            retlst.append([tname, fil])
                    else:
                        continue

        retlst = list(sorted(retlst, key = lambda tn : tn[0]))
        if len(retlst) in [2,5,8]:
            return retlst

        return None
    
    def __window_data_assembler__(self, build, depth):
        ''' Organize raw data into dataframe - Options: File_Direct, Folder_Info, File_Info '''

        global data
        
        exts, errs = self.Extension_List, self.Error_List
        base, bpath = self._ppath(self.N_Dir).root, self.N_Dir
        folen, filen, exlen, errlen = len(self.Folder_List), len(self.File_List), len(self.Extension_List), len(self.Error_List)
        fols, fils = [str(bpath) + base + str(fo) for fo in self.Folder_List], [str(bpath) + base + str(fi) for fi in self.File_List]
        foldata, fildata = [dict([(str(fod[0]),dict(zip(self.osfields,list(fod[1]))))]) for fod in self.Folder_Data], [dict([(str(fid[0]),dict(zip(self.osfields,list(fid[1]))))]) for fid in self.File_Data]

        if self._fz.ratio(build,"File_Direct") > 90:
            datalist = [pa.split("\\") for pa in fils]
            datalist = list(zip(*self._ziplong(*datalist)))
            dataframe = self._pd.DataFrame(datalist,range(len(datalist)), columns= ["Parent "+str(ct) for ct in range(len(max(datalist, key=lambda chld: len(chld))))])

            return dataframe

        elif self._fz.ratio(build, "Folder_Info") > 85:
            field = list(list(foldata[0].values())[0].keys())
            folders = [list(fold.keys())[0] for fold in foldata]
            data = [list(list(fold.values())[0].values()) for fold in foldata]
            for dset in range(len(data)):
                try:
                    data[dset] = data[dset]+[min([str(p) for p in self.Folder_List if str(data[dset][0]) in str(p)], key=lambda pt: len(str(pt)))]
                except ValueError:
                    continue
                
            dataframe = self._pd.DataFrame(data=data, index=folders, columns=field)   
            for cols in dataframe.columns:
                if 'time' in cols:
                    try:
                        dataframe[cols] = [self._dime(cdate) for cdate in dataframe[cols].tolist()]
                    except TypeError:
                        continue
                elif 'size' in cols:
                    dataframe[cols] = [n/1000 for n in dataframe[cols].tolist()]

            return dataframe
            
        elif self._fz.ratio(build, "File_Info") > 75:
            field = list(list(fildata[0].values())[0].keys())
            folders = [list(fild.keys())[0] for fild in fildata]
            data = [list(list(fild.values())[0].values()) for fild in fildata]
            for dset in range(len(data)):
                try:
                    data[dset] = data[dset]+[min([str(p) for p in self.File_List if str(data[dset][0]) in str(p)], key=lambda pt: len(str(pt)))]
                except ValueError:
                    continue
                
            dataframe = self._pd.DataFrame(data=data, index=folders, columns=field)
            for cols in dataframe.columns:
                if 'time' in cols:
                    try:
                        dataframe[cols] = [self._dime(cdate) for cdate in dataframe[cols].tolist()]
                    except TypeError:
                        continue
                elif 'size' in cols:
                    dataframe[cols] = [n/1000 for n in dataframe[cols].tolist()]

            return dataframe

        elif build == "":
            
            return []
        
        else:
            raise InvalidError("Input not recognized. Please use one of the following 'File_Direct', 'Folder_Direct', or 'File_Infor'")

        return dataframe

    def __window_data_saver__(self, file_id, data, filpath):
        ''' Save any current data in instance with "id" + default name '''
        
        tdate = datetime.datetime.today().strftime("%Y-%m-%d")
        if file_id != "": file_id += ' - ' if file_id[-1] != ' ' else ''
        dloc = list(locals().items())
        os.chdir(filpath)
        
        xls = [f'{file_id}FileMinerData {tdate}.xls', [('FolderPaths',self.Folder_List), ('FolderData', self.Folder_Data), ('FilePaths', self.File_List), ('FileData', self.File_Data), ('Extensions', self.Extension_Data), ('Changes', self.Modification_Log)]]
        pke = [(f'{file_id}FolderDataFrame {tdate}.', self.Folder_Data_Frame), (f'{file_id}FileDataFrame {tdate}.', self.File_Data_Frame), [f'{file_id}InfoDataFrame {tdate}.', self.Info_Data_Frame]]
        txt = [[f'{file_id}FolderPaths {tdate}.txt', self.Folder_List], [f'{file_id}FilePaths {tdate}.txt',self.File_List]]
                                                          
        if data[0]:
            if xls[0] in self._dlst(): self.Delete(xls[0])
            databook = xlwt.Workbook()
            for shts, data in xls[1]:
                if data != []:
                    sht = wb.add_sheets(shts)
                    for cnt in range(len(data)):
                        sht.write(cnt + 1, 1, cnt + 1)
                        sht.write(cnt + 1, 2, data[cnt].split("\\")[-1])
                        sht.write(cnt + 1, 3, data[cnt])
                    self.Saved_Data_Files += list(filter( lambda loc : loc[1] == data, dloc))[0][0]
            databook.save(xls[0])                    

        if data[1]:
            for nm, df in pke:
                if df != []:
                    df.to_pickle(nm + 'pickle')
                    df.to_excel(nm + 'xls')
                    self.Saved_Data_Files += list(filter( lambda loc : loc[1] == df, dloc))[0][0]

        if data[2]:
            for nm, tx in txt:
                if tx != []:
                    with open(nm, 'w+') as tf:
                        tf.write(tx)
                    nm.save()
                    nm.close()
                    self.Saved_Data_Files += list(filter( lambda loc : loc[1] == tx, dloc))[0][0]

    def __window_file_modifier__(self, modlst, chgtxt, specrmv):
        ''' Modify file names as requested '''

        if modlst != []:
            opth, npth, isext = "", "", False
            for pth in modlst:
                opth = pth.split("\\")[-1]
                if '.' in opth:
                    tempx, isext = opth.split('.')[-1], True
                p = '\\'.join(pth.split("\\")[:-1])+'\\'
                npth = opth
                if chgtxt:
                    for otxt in self.Modification_Matrix.keys():
                        ntxt = self.Modification_Matrix.get(otxt)
                        if isinstance(ntxt,str):
                            npth = npth.replace(otxt,ntxt)
                        elif isinstance(ntxt,list):
                            for nt in ntxt:
                                npth = npth.replace(otxt,nt)
                        else:
                            pass
                if isext:
                    npth = npth.split('.')[0] + f'.{tempx}'
                if specrmv:
                    for char in self.Character_Removal_Targets:
                        if isinstance(char,list) and char[0] not in npth:
                            npth = npth.replace(char[1],"")
                        elif isinstance(char,str):
                            npth = npth.replace(char,"")
                try:
                    self.Modify(p+opth,p+npth)
                    self.Modication_Log += [[p+opth, opth, npth, "Success"]]
                except FileNotFoundError:
                    self.Modication_Log += [[p+opth, opth, npth, "Failure"]]
            
        return "Modfications Complete!"

    def __get_data_size__(self, obj):
        ''' Return size of class objects in Mbs '''

        obj_size = 0
        if obj == "Lists":
            for obs in [self.Folder_List, self.File_List, self.Extension_List, self.Error_List]:
                obj_size += sys.getsizeof(obs)
                
        elif obj == "DataSets":
            for obs in [self.Folder_Data, self.File_Data, self.Extension_Data]:
                obj_size += sys.getsizeof(obs)
                
        elif obj == "DataFrames":
            for obs in [self.Folder_Data_Frame, self.File_Data_Frame, self.Info_Data_Frame]:
                obj_size += sys.getsizeof(obs)
                
        elif obj == "Logs":
            for obs in [self.Filtered_Folders, self.Filtered_Files, self.Modification_Matrix, self.Character_Removal_Targets, self.Modification_Log, self.Saved_Data_Files]:
                obj_size += sys.getsizeof(obs)
                
        if obj_size > 0:
            obj_size = obj_size/1000
            
            return obj_size
        
        return 0
    
    def GetData(self, Initial_Path = "", Collect_Statistics = True, Auto_Build = False, Print_Updates = False, Load_Data_Id = ""):
        ''' Extracts initial data from target '''

        if Load_Data_Id == "":
            if Initial_Path == "":
                Initial_Path == self.N_Dir
            self.Timer = time.time()
            
            if Collect_Statistics:
                self.Folder_List, self.File_List, self.Extension_List, self.Error_List, self.Folder_Data, self.File_Data, self.Extension_Data = self.__window_data_extract__(start = Initial_Path, filstats = Collect_Statistics, prntrecs = Print_Updates)
            else:
                self.Folder_List, self.File_List, self.Extension_List = self.__window_data_extract__(start = Initial_Path, filstats = Collect_Statistics, prntrecs = Print_Updates)
            if Auto_Build == True:
                self.DataSet = self.BuildView()
                
            return "Complete: Runtime = %.2f Minutes" % int((time.time()-self.Timer)/60)
        
        elif Load_Data_Id != "":
            Master_Set = __window_data_load__(Load_Data_Id)
            if len(Master_Set) == 2:
                self.Folder_List, self.File_List = Master_Set
                
                return 'File and Folder Lists Extracted: Please run "GetData" to generate Data Profiles'

            if len(Master_Set) == 5:
                self.Folder_List, self.File_List, self.Error_List, self.Folder_Data, self.File_Data, self.Extension_Data = Master_Set
                
                return 'File and Folder Data Extracted: Please run "BuildView" to generate Dataframes'
            
            elif len(Master_Set) == 8:
                self.Folder_List, self.File_List, self.Extension_List, self.Error_List, self.Folder_Data, self.File_Data, self.Extension_Data, self.Folder_Data_Frame, self.File_Data_Frame = Master_Set
                
                return 'Data Load Complete: All files found'
            
            return 'No saved files found: Checked saved files or run "GetData" to generate new Dataset'
        
    def BuildView(self, Build_Data_Type = ['File_Direct', 'File_Info', 'Folder_Info'], Index_Depth = 0):
        ''' Builds dataframe from existing data in class instance '''

        dflst = [self.Info_Data_Frame, self.File_Data_Frame, self.Folder_Data_Frame]
        deflst = ['File_Direct', 'File_Info', 'Folder_Info']

        if type(Build_Data_Type) == str:
            Build_Data_Type = [bdt if Build_Data_Type in bdt else "" for bdt in deflst]

        for df,b in zip(dflst,Build_Data_Type):
            if self._fz.ratio('File_Direct',b) > 85:
                if df: print("Info DataFrame if Being Updated")
                self.Info_Data_Frame = self.__window_data_assembler__(b, Index_Depth)
                
            elif  self._fz.ratio('File_Info',b) > 85:
                if df: print("File DataFrame if Being Updated")
                self.File_Data_Frame = self.__window_data_assembler__(b, Index_Depth)
                
            elif  self._fz.ratio('Folder_Info',b) > 85:
                if df: print("Folder DataFrame if Being Updated")
                self.Folder_Data_Frame = self.__window_data_assembler__(b, Index_Depth)
                
        return "DataFrames Accessible Through Class Instance By their Designation [Info_Data_Frame, File_Data_Frame, Folder_Data_Frame]"
   
    def AddUpdater(self, Old_Value_Set = [], New_Value_Set = [], Target_Extension="", Remove = False):
        ''' Update change values for class instances '''

        if not Remove:
            self.__update_mod_matrix__(Old_Value_Set, New_Value_Set)

        else:
            if Old_Value_Set == []:
                if New_Value_Set != []:
                    self.__update_char_tar__(New_Value_Set, Target_Extension)
                    print("Removal Set Not Detected so New Value set was used\nPlease check these values to ensure they are correct.")
                    
                    return None
                
                print("No values detected, please input a removal set to add to the removal text set")
            else:
                self.__update_char_tar(Old_Value_Set, Target_Extension)
                print("Removal set updated with targets")
                
                return None
            
        pass
    
    def ModifyFiles(self, Target_Path = "", Target_Phrase ="", Target_Extension = "", Change_Text = True, Remove_Special = False, Preview_Prompt = False):
        ''' Make modification to file names if any have been submitted '''

        if Target_Path == "": Target_Path = self.N_Dir
        Modification_File_List = []
        selt.Timer = time.time()

        if self.Info_Data_Frame != []:
            for index, row in self.Info_Data_Frame.iterrows():
                if '.' in ''.join(row):
                    rd = [prt for prt in row.tolist() if not prt.isnull()]
                    multipath = ['\\'.join(rd[:x]) for x in range(len(rd))]
                    for mp in multipath:
                        if Target_Path in multipath:
                            Modification_File_List.append(multipath[-1])
                            continue
                    if Target_Phrase in rd:
                        if ''.join(rd) not in Modificatoin_File_List: Modification_File_List.append(''.join(rd))
                    
            if Modification_File_List:
                    if Preview_Prompt:
                        print(Modification_File_List[0:5])
                        Response = input("Sample shown, would you like to continue? ['y','n']\n")
                        while Response != 'y' or Response != 'n':
                            Response = input("Invalid Input:\nTo continue type 'y' to exit type 'n'\n")
                        if Respons == 'n':
                            print("\nProcess Terminated")
                            
                            return None
                        
                    self.__window_file_modifier__(Modification_File_List, Change_Text, Remove_Special)
                    Completion_Prompt = "Complete: Runtime = %.2f Minutes" % int((time.time()-self.Timer)/60)
                    print(Completion_Prompt)
                    
                    return Completion_Prompt
                
            else:
                print("No file found with Path and Target Text Combination. Please reveiw entries")
        else:
            print("No data detected in Folder Data, Please run the 'BuildView' utility to construct DataFrame basis")
            
        return None
    
    def ModifyFolders(self, Target_Path = "", Target_Phrase ="", Target_Extension = "", Change_Text = True, Remove_Special = False, Preview_Prompt = False):
        ''' Make modification to folder names if any have been submitted '''

        if Target_Path == "": Target_Path = self.N_Dir
        Modification_Folder_List = []
        selt.Timer = time.time()
        
        if self.Folder_Data_Frame != []:
            for index, row in self.Folder_Data_Frame.iterrows():
                if '.' not in ''.join(row):
                    rd = [prt for prt in row.tolist() if not prt.isnull()]
                    multipath = ['\\'.join(rd[:x]) for x in range(len(rd))]
                    for mp in multipath:
                        if Target_Path in multipath:
                            Modification_Folder_List.append(multipath[-1])
                            continue
                    if Target_Phrase in rd:
                        if ''.join(rd) not in Modification_Folder_List: Modification_Folder_List.append(''.join(rd))
                    
            if Modification_Folder_List:
                    if Preview_Prompt:
                        print(Modification_Folder_List[0:5])
                        Response = input("Sample shown, would you like to continue? ['y','n']\n")
                        while Response != 'y' or Response != 'n':
                            Response = input("Invalid Input:\nTo continue type 'y' to exit type 'n'\n")
                        if Respons == 'n':
                            print("\nProcess Terminated")
                            
                            return None
                        
                    self.__window_file_modifier__(Modification_Folder_List, Change_Text, Remove_Special)
                    Completion_Prompt = "Complete: Runtime = %.2f Minutes" % int((time.time()-self.Timer)/60)
                    print(Completion_Prompt)
                    
                    return Completion_Prompt
            else:
                print("No folder found with Path and Target Text Combination. Please reveiw entries")
        else:
            print("No data detected in Folder Data, Please run the 'BuildView' utility to construct DataFrame basis")
            
        return None
        
    def SearchFiles(self, Target = "", Method = "Contains"):
        ''' Return a structured list of files given specific criteria '''

        filteredfiles = []
        if self.File_List != []:
            if Method == "Contains":
                filteredfiles = [str(filtar) for filtar in self.File_List if Target in str(filtar)]
            elif Method == "Equals":
                filteredfiles = [str(filtar) for filtar in self.File_List if any(Target == fil for fil in str(filtar).split("\\"))]
            else:
                raise InvalidInputError("Please use one of the following options ['Contains','Equals']")

            if filteredfiles:
                self.Filtered_Files = filteredfiles
                print(f'Number of files found: {len(filteredfiles)}')
                
                return filteredfiles
            
            print("No Folders found that {} {}".format(Method[:-1],Target))
            
            return None
        
        else:
            raise EmptySetError("No Data Present in File List.\nPlease run the GetData() method with a target location or create a new instance with 'Collect_Explorer' set to True")

    def SearchFolders(self, Target = "", Method = "Contains"):
        ''' Return a structured list of folders given specific criteria '''

        filteredfolders = []
        if self.Folder_List != []:
            if Method == "Contains":
                filteredfolders = [str(foltar) for foltar in self.Folder_List if Target in str(foltar)]
            elif Method == "Equals":
                filteredfolders = [str(foltar) for foltar in self.Folder_List if any(Target == fol for fol in str(foltar).split("\\"))]
            else:
                raise InvalidInputError("Please use one of the following options ['Contains','Equals']")

            if filteredfolders:
                self.Filtered_Folders = filteredfolders
                print(f'Number of files found: {len(filteredfolders)}')
                
                return filteredfolders
            
            print("No Folders found that {} {}".format(Method[:-1],Target))
            
            return None
        
        else:
            raise EmptySetError("No Data Present in Folder List.\nPlease run the GetData() method with a target location or create a new instance with 'Collect_Explorer' set to True")
            
    def Navigate2File(self, Target_Path = '', Target_Extension = ''):
        ''' Displays list of file options from search results '''

        retfiles, usel, shw = list(enumerate([fl for fl in self.File_List if Target_Path in fl])), "", 10

        if retfiles:
            while usel not in [no[0] for no in retfiles] + ["Quit()", "ShowAll()"]:
                print(''.join(['. '.join(itm) for itm in retfiles[shw-10:sh2]], '\n'))
                usel = input("Please Select Number of File to Open: ")
                if usel == "More()":
                    shw = shw + 10

            if usel == 'ShowAll()':
                print(''.join(['. '.join(itm) for itm in retfiles[shw-10:sh2]], '\n'))
                usel = input("Please choose a file or Quit() to Cancel\n")

            if usel == "Quit()":
                return

            Target_Location = retfiles[int(usel)][1]
            filopen(Target_Location, 'open')
            
            return "File Opened: " + Target_Location

        return "No Files Found"

    def Navigate2Folder(self, Target_Path = ''):
        ''' Displays list of folder options from search results '''
        
        retfiles, usel, shw = list(enumerate([fl for fl in self.Folder_List if Target_Path in fl])), "", 10

        if retfiles:
            while usel not in [no[0] for no in retfiles] + ["Quit()", "More()", "ShowAll()"]:
                print(''.join(['. '.join(itm) for itm in retfiles[shw-10:sh2]], '\n'))
                usel = input("Please Select Number of Folder to Open: ")
                if usel == "More()":
                    shw = shw + 10
                
            if usel == 'ShowAll()':
                print(''.join(['. '.join(itm) for itm in retfiles[shw-10:sh2]], '\n'))
                usel = input("Please choose a folder or Quit() to Cancel\n")

            if usel == "Quit()":
                return

            Target_Location = retfiles[int(usel)][1]
            folopen(f'explorer /select "{Target_Location}"')

            return "Folder Opened: " + Target_Location

        return "No Folders Found"
        
    def ExportData(self, Run_ID = "", Excel = False, Pickle = False, Text = False, Path = ""):
        ''' Creates data export files in given format if supplied with a name'''

        if Path == '': Path = self.N_Dir
        self.Timer = time.time()
        Option_List = [Excel, Pickle, Text]

        self.__window_data_saver__(Run_ID, Option_List, Path)
        
        return "Complete: Runtime = %.2f Minutes" % int((time.time()-self.Timer)/60)


fildig = FileMiner('G:\\Transfered Files From USB-Phone-Computer\\Unrelated to current courses', True)
