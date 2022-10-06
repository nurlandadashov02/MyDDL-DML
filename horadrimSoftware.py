import os
import time
import csv
import sys
from language import LanguageOperations
from systemCatalogue import SystemCatalogue
from bplustree import indeces

if not os.path.exists("SystemCatalogue.csv"):
    SystemCatalogue.initialize()

inp = open(sys.argv[1], "r")
out = open(sys.argv[2], "w")

lines = [line.rstrip() for line in inp]

f = open("horadrimLog.csv", "a", newline='')
writer = csv.writer(f)

def log(line, isCreated):
    writer.writerow([int(time.time()), line, 'success' if isCreated else 'failure'])

for line in lines:
    if not line:
        continue
    try:
        words = line.split()
        if words[0] == 'create' and words[1] == 'type':
            type_name = words[2]
            num_fields = words[3]
            pkey = int(words[4])
            fields = words[5:]
            rows = [] 
            for position, (name, type) in enumerate(zip(*[iter(fields)] * 2)):
                if position + 1 != pkey:
                    rows.append([type_name, position, name, type])
                else:
                    rows.insert(0, [type_name, position, name, type])

            isCreated = LanguageOperations.createType(type_name, rows)
            log(line, isCreated)
        elif words[0] == 'delete' and words[1] == 'type':
            type = words[2]
            isDeleted = LanguageOperations.deleteType(type)
            log(line, isDeleted)
        elif words[0] == 'list' and words[1] == 'type':
            types = LanguageOperations.listType()
            isListed = False
            if types:
                isListed = True
                for type in types:
                    out.write(type + '\n')
            log(line, isListed)
        elif words[0] == 'create' and words[1] == 'record':
            type = words[2]
            field_values = words[3:]
            isCreated = LanguageOperations.createRecord(type, field_values)
            log(line, isCreated)
        elif words[0] == 'delete' and words[1] == 'record':
            type = words[2]
            pkey = words[3]
            isDeleted = LanguageOperations.deleteRecord(type, pkey)
            log(line, isDeleted)
        elif words[0] == 'update':
            type = words[2]
            pkey = words[3]
            field_values = words[4:]
            isUpdated = LanguageOperations.updateRecord(type, pkey, field_values)
            log(line, isUpdated)
        elif words[0] == 'search':
            type = words[2]
            pkey = words[3]
            field = LanguageOperations.searchRecord(type, pkey)
            found = False
            if field:
                out.write(field + '\n')
                found = True
            log(line, found)
            
        elif words[0] == 'list' and words[1] == 'record':
            type = words[2]
            records = LanguageOperations.listRecord(type)
            isListed = False
            if records:
                isListed = True
                for record in records:
                    out.write(record + '\n')
            log(line, isListed)
        elif words[0] == 'filter':
            type = words[2]
            condition = words[3]

            selected = ""
            if '>' in condition:
                selected = '>'
            elif '<' in condition:
                selected = '<'
            elif '=' in condition:
                selected = '='

            field_name, value = condition.split(selected)
            records = LanguageOperations.filterRecord(type, field_name, value, selected)
            isFiltered = False
            if records:
                isFiltered = True
                for record in records:
                    out.write(record + '\n')
            log(line, isFiltered)
    except(Exception) as e:
        log(line, False)


for tree in list(indeces.values()):
    tree.saveTree()

inp.close()
out.close()
f.close()