import json
import csv
import logging
# import warcio

def output_json(outputfile, scoredata, collectionmodel):
    json.dump(scoredata, outputfile, indent=4)

def output_datafile(outputfile, scoredata, collectionmodel):
    
    outputdata = []

    seedid = 0

    for urit in scoredata["timemaps"]:

        seedid += 1

        for urim in scoredata["timemaps"][urit]:

            outputrow = {}

            try:
                if scoredata["timemaps"][urit][urim]["overall topic status"] == \
                    "off-topic":
                    label = 0

                else:
                    label = 1

            except KeyError as e:
                label = repr(e)

            fronturim = urim[:urim.find('/http')]

            if fronturim[-3:] == 'id_':
                fronturim = fronturim[:-3]

            outputrow["date"] = fronturim[fronturim.rfind('/') + 1:]
            outputrow["id"] = seedid
            outputrow["URI"] = urim
            outputrow["label"] = label

            outputdata.append(outputrow)

    fieldnames = [ 'id', 'date', 'URI', 'label' ]

    writer = csv.DictWriter(outputfile, fieldnames=fieldnames, delimiter='\t')

    writer.writeheader()

    for row in outputdata:
        writer.writerow(row)

# def output_wat(outputfile, jsondata, collectionmodel):
    
    # TODO: the "Payload-Metadata" part of the WAT file could be a place to put our scoring data
    # pass

supported_output_types = {
    # 'wat': output_wat,
    'json': output_json,
    'golddatafile': output_datafile
}