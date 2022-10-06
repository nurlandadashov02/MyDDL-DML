import os
import csv
import pandas as pd
from constants import *

class StorageManager:
    @staticmethod
    def createFile(path_name):
        path = os.path.join("data", path_name)
        os.makedirs(path, exist_ok=True)
        files = os.listdir(path)
        files.remove("page_data.csv")
        if len(files) == 0:
            name = '0.txt'
        else:
            names = [int(x.split(".")[0]) for x in files]
            names.sort()
            name = f'{names[-1] + 1}.txt'
        with open(os.path.join(path, name), 'a') as f:
            for _ in range(NUM_PAGES):
                f.write("0" * PAGE_HEADER)
                f.write(" " * (PAGE_SIZE - PAGE_HEADER))
        with open(os.path.join(path, 'page_data.csv'), 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, *([NUM_RECORDS] * NUM_PAGES)])

    @staticmethod
    def createPageData(type):
        path = os.path.join("data", type)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, 'page_data.csv'), "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["file_name", *[f"page{i}" for i in range(NUM_PAGES)]])
            writer.writeheader()

    @staticmethod
    def findEmptyPage(type):
        path = os.path.join("data", type)
        os.makedirs(path, exist_ok=True)
        found = {
            'file': '',
            'page': -1
        }
        csv_path = os.path.join(path, 'page_data.csv')
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            emptyPageCount = 0
            row_id = -1
            for i, row in enumerate(reader):
                for page in list(row.keys())[1:]:
                    if int(row[page]) > 0:
                        found['file'] = row['file_name']
                        found['page'] = int(page[4])
                        emptyPageCount = int(row[page]) - 1
                        row_id = i
                        break
                    
                if found['file'] and found['page'] != -1:
                    break

        if found['file'] and found['page'] != -1:
            df = pd.read_csv(csv_path)
            df.loc[row_id, f"page{found['page']}"] = emptyPageCount
            df.to_csv(csv_path, index=False)
            return found

        return False

    @staticmethod
    def updateEmptyPages(type, value):
        [fileName, pageIndex, _] = value
        path = os.path.join("data", type)
        os.makedirs(path, exist_ok=True)
        csv_path = os.path.join(path, 'page_data.csv')
        df = pd.read_csv(csv_path)
        row_id = int(fileName.split(".")[0])
        df.loc[row_id, f"page{pageIndex}"] += 1 

        delete = True
        for i in range(NUM_PAGES):
            if df.loc[row_id, f"page{i}"] != NUM_RECORDS:
                delete = False
                break

        if delete:
            df.drop(row_id, axis=0, inplace=True)
            os.remove(os.path.join(path, fileName))

        df.to_csv(csv_path, index=False)