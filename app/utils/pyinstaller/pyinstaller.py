import os
import struct
import marshal
import zlib
import sys
from .pyinstallerExceptions import ExtractionError

class CTOCEntry:
    __slots__ = ['name', 'entrysize', 'offset', 'compsize', 'flag', 'typecompressed', 'spos']
    def __init__(self, name, entrysize, offset, compsize, flag, typecompressed, spos):
        self.name = name
        self.entrysize = entrysize
        self.offset = offset
        self.compsize = compsize
        self.flag = flag
        self.typecompressed = typecompressed
        self.spos = spos

class PyInstArchive:
    def __init__(self, path):
        self.filePath = path
        self.pycMagic = b'\0' * 4
        self.pyinstVer = 0
        self.pymaj = 0
        self.pymin = 0
        self.overlaySize = 0
        self.overlayPos = 0
        self.entrypoints = []
        
    def open(self):
        try:
            self.fPtr = open(self.filePath, 'rb')
            self.fPtr.seek(-4, 2)
            self.overlaySize = struct.unpack('!I', self.fPtr.read(4))[0]
            self.fPtr.seek(-8, 2)
            magic = self.fPtr.read(4)
            if magic != b'PYZ\0':
                raise ExtractionError("Invalid PyInstaller archive")
            self.fPtr.seek(-(self.overlaySize + 8), 2)
            self.overlayPos = self.fPtr.tell()
        except Exception as e:
            raise ExtractionError(f"Error opening file: {str(e)}")
    
    def parseTOC(self):
        try:
            self.fPtr.seek(self.overlayPos)
            toc = marshal.load(self.fPtr)
            for entry in toc:
                (name, entrysize, offset, compsize, flag, typecompressed, spos) = entry
                self.entrypoints.append(name)
                ce = CTOCEntry(name, entrysize, offset, compsize, flag, typecompressed, spos)
                if ce.typecompressed == 0:
                    ce.typecompressed = 's'  # s for uncompressed
                elif ce.typecompressed == 1:
                    ce.typecompressed = 'z'  # z for zlib
                else:
                    ce.typecompressed = '?'  # ? for unknown
        except Exception as e:
            raise ExtractionError(f"Error parsing TOC: {str(e)}")
    
    def extractFiles(self):
        try:
            for entry in self.entrypoints:
                self.fPtr.seek(entry.offset)
                data = self.fPtr.read(entry.compsize)
                if entry.typecompressed == 'z':
                    data = zlib.decompress(data)
                with open(entry.name, 'wb') as f:
                    f.write(data)
        except Exception as e:
            raise ExtractionError(f"Error extracting files: {str(e)}")
    
    def close(self):
        self.fPtr.close()

def ExtractPYInstaller(path):
    try:
        arch = PyInstArchive(path)
        arch.open()
        arch.parseTOC()
        return arch
    except Exception as e:
        raise ExtractionError(str(e))