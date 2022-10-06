from constants import *

class FileReader:
    def __init__(self, path):
        self.path = path

    def readPage(self, index):
        f = open(self.path, 'rt')
        f.seek(index * PAGE_SIZE)
        buffer = f.read(PAGE_SIZE)
        f.close()
        return buffer

    def replaceHeader(self, pageIndex, recordIndex, value):
        with open(self.path, 'rt') as f:
            f.seek(pageIndex * PAGE_SIZE)
            header = f.read(PAGE_HEADER)
            new_header = header[:recordIndex] + value + header[recordIndex + 1:]
            header = header.replace(header, new_header)
        
        with open(self.path, 'r+') as f:
            f.seek(pageIndex * PAGE_SIZE)
            f.write(header)

    def writeRecord(self, pageIndex, recordIndex, record):
        self.replaceHeader(pageIndex, recordIndex, "1")        
        with open(self.path, 'r+') as f:
            f.seek(pageIndex * PAGE_SIZE + PAGE_HEADER + recordIndex * RECORD_SIZE)
            f.write(record)

    def deleteRecord(self, pageIndex, recordIndex):
        self.replaceHeader(pageIndex, recordIndex, "0")  


# reader = FileReader("test.txt")
# reader.writeRecord(0, 5, "2")