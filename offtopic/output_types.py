import json
import csv
import logging

def output_json(outputfile, jsondata, collectionmodel):
    json.dump(jsondata, outputfile, indent=4)

def output_datafile(outputfile, jsondata, collectionmodel):
    
    outputdata = []

    seedid = 0

    for measure in jsondata:

        for urit in jsondata[measure]["timemaps"]:

            seedid += 1

            for urim in jsondata[measure]["timemaps"][urit]:

                outputrow = {}

                # if 'id_/http' in urim:
                #     urim = urim.replace('id_/http', '/http')

                fronturim = urim[:urim.find('/http')]

                if fronturim[-3:] == 'id_':
                    fronturim = fronturim[:-3]

                outputrow["date"] = fronturim[fronturim.rfind('/') + 1:]

                if jsondata[measure]["timemaps"][urit][urim]["on-topic"] == True:
                    outputrow["label"] = 1
                else:
                    outputrow["label"] = 0

                outputrow["id"] = seedid
                outputrow["URI"] = urim

                outputdata.append(outputrow)    

    fieldnames = [ 'id', 'date', 'URI', 'label' ]

    writer = csv.DictWriter(outputfile, fieldnames=fieldnames, delimiter='\t')

    writer.writeheader()

    for row in outputdata:
        writer.writerow(row)

supported_output_types = {
    # 'wat': output_wat,
    'json': output_json,
    'datafile': output_datafile
}