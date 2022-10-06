import csv
import pandas as pd

class SystemCatalogue:
    @staticmethod
    def initialize():
        with open("SystemCatalogue.csv", "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["rel_name", "position", "attr_name", "type"])
            writer.writeheader()

    @staticmethod
    def addType(rows):
        with open("SystemCatalogue.csv", "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    @staticmethod
    def deleteType(type):
        file = "SystemCatalogue.csv"
        df = pd.read_csv(file)
        df = df[df["rel_name"] != type]
        df.to_csv(file, index=False)

    @staticmethod
    def getFields(type):
        with open("SystemCatalogue.csv", "r") as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader if row['rel_name'] == type]
            return rows

    @staticmethod
    def transformFields(type, fields):
        field_infos = SystemCatalogue.getFields(type)
        field_infos.sort(key=lambda x: int(x['position']))
        for i, field_info in enumerate(field_infos):
            if field_info['type'] == 'int':
                fields[i] = int(fields[i])

        return fields
    
    @staticmethod
    def transformPKey(type, pkey):
        field_infos = SystemCatalogue.getFields(type)
        field_infos.sort(key=lambda x: int(x['position']))
        if field_infos[0]['type'] == 'int':
            return int(pkey)
        else:
            return pkey

    @staticmethod
    def getPrimaryKey(type, fields):
        with open("SystemCatalogue.csv", "r") as f:
            reader = csv.DictReader(f)
            pkey_name = ''
            pkey_position = -1
            for row in reader:
                 if row['rel_name'] == type:
                    pkey_name = row['attr_name']
                    pkey_position = int(row['position'])
                    break
            return fields[pkey_position]
