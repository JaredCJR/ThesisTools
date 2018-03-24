#!/usr/bin/env python3
import os
import csv

if __name__ == '__main__':
    key_1 = "Original-1-thread"
    key_2 = "Original-12-threads"
    key_3 = "ABC-1-thread"
    key_4 = "ABC-12-threads"
    TargetDict = None
    
    prefix = "./data"
    ListOfData = []
    for root, dirs ,files in os.walk(prefix):
        for file in files:
            ListOfData.append(root + '/' + file)

    '''
    Sort into TargetDict={'target': {key_1:[...], key_2:[...], ...}}
    '''
    for csvFile in ListOfData:
        csvData = csv.DictReader(open(csvFile))
        for row in csvData:
            if TargetDict is None:
                TargetDict = {}
            if row['target'] not in TargetDict:
                TargetDict[row['target']] = {}
            if key_1 not in TargetDict[row['target']]:
                TargetDict[row['target']][key_1] = []
                TargetDict[row['target']][key_2] = []
                TargetDict[row['target']][key_3] = []
                TargetDict[row['target']][key_4] = []
            if float(row[key_1]) != -1:
                TargetDict[row['target']][key_1].append(float(row[key_1]))
            if float(row[key_2]) != -1:
                TargetDict[row['target']][key_2].append(float(row[key_2]))
            if float(row[key_3]) != -1:
                TargetDict[row['target']][key_3].append(float(row[key_3]))
            if float(row[key_4]) != -1:
                TargetDict[row['target']][key_4].append(float(row[key_4]))
    '''
    get average for all keys
    finalDict = {'target': { key_1: value, ...}}
    '''
    finalDict = {}
    for target, data in TargetDict.items():
        finalDict[target] = {}
        for key, listOfVals in data.items():
            finalDict[target][key] = sum(listOfVals) / float(len(listOfVals))
    '''
    write to csv file
    '''
    fieldnames = ['target', key_1, key_2, key_3, key_4]
    with open('BuildAvgTime.csv', 'w', newline='') as csv_file: 
        writer = csv.DictWriter(csv_file, fieldnames = fieldnames) 
        writer.writeheader()
        for target, avg_times in finalDict.items():
            tmp = avg_times
            tmp['target'] = target
            writer.writerow(tmp)


