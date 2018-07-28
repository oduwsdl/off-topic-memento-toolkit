[![Build Status](https://travis-ci.org/oduwsdl/off-topic-memento-toolkit.svg?branch=master)](https://travis-ci.org/oduwsdl/off-topic-memento-toolkit)

Given a collection of archived web pages, known as mementos, the Off Topic Memento Toolkit (OTMT) allows one to determine which mementos are off-topic. Mementos are produced by crawling live web pages, resulting in collections that often contain different versions of the same web page. In time, due to hacking, loss of ownership of the domain, or even website restructuring, a web page can go off-topic, resulting in the collection containing off-topic mementos. The OTMT helps users detect these off-topic mementos before conducting research on their collections of archived web pages.

This code is based on work by:

AlNoamany, Y., Weigle, M.C. & Nelson, M.L. Detecting off-topic pages within TimeMaps in Web archives. *International Journal on Digital Libraries* (2016) 17: 203. https://doi.org/10.1007/s00799-016-0183-5

and an early version of it was evaluated in:

Jones, S.M., Weigle, M.C & Nelson, M.L. The Off-Topic Memento Toolkit. *Proceedings of the 15th International Conference on Digital Preservation* (2018) https://arxiv.org/abs/1806.06870

# Quick start

The software is now available on PyPI **and requires a minimum of Python 3.6**:

`pip install otmt`

This installs the `detect_off_topic` command on your system, along with the `offtopic` Python library. To determine if the content in Archive-It collection is off-topic:

`detect_off_topic -i archiveit=7877 -o outputfile.json`

This stores the information about each memento and TimeMap of Archive-It collection 7877 in a JSON-formatted file named `output.json`.

# More details

## Input types

To accomplish this, OTMT accepts the following inputs:
* an Archive-It collection ID
* URIs for one or more Memento TimeMaps (see RFC 7089)
* one or more files in Web ARChive (WARC) format (see ISO 28500)

These inputs are converted internally into a series of files and folders used for the rest of the evaluation.

To specify an Archive-It collection use the `archiveit` keyword followed by an = and the collection ID, like so:
`detect_off_topic -i archiveit=7877 -o outputfile.json`

For one or more TimeMaps, specify them with the `timemap` keyword followed by an = and the URI-T of the TimeMap:
`detect_off_topic -i timemap=http://archive.example.org/timemap1,http://archive.example.org/timemap2 -o outputfile.json`

Likewise, for one or more WARC files:
`detect_off_topic -i warc=example1.warc.gz,example2.warc.gz -o outputfile.json`

### Notes For WARCs:
When analyzing WARCs, OTMT:
1. generates a TimeMap for each seed it encounters
2. generates an entry in this TimeMap for the seed with an internal URI-M and a memento-datetime derived from record's WARC-Date header
3. once done with all WARCs, presents the TimeMaps as if they had been downloaded to the measure part of the architecture
4. The measure part of the architecture (currently) takes the first memento and compares it to each other memento in the TimeMap

In summary, OTMT pulls in all of the data from all WARCs and analyzes it together. For TimeMap Measures, it uses the first memento in the TimeMap as the basis for comparison with other mementos in the TimeMap.

There is no URI canonicalization like the Internet Archive does with URIs like edition.cnn.com and www.cnn.com. OTMT does not compare example.org and example2.org because they would have separate URI-Rs and hence separate TimeMaps.

### Notes For TimeMaps:

In this case, OTMT does not aggregate data from all TimeMaps, instead treating them separately. If two TimeMaps serve the same URI-R, then OTMT does not reconcile them into one. Such functionality would indeed be useful. If added, one could compare TimeMaps for the same URI-R across multiple collections or even multiple archives. If this functionality is desired, [please request it as a feature](https://github.com/oduwsdl/off-topic-memento-toolkit/issues).

## TimeMap Measures
With TimeMap measures, each memento in a TimeMap is compared to the first memento of that TimeMap. The comparison is performed using one or more of the following measures:
* Cosine Similarity (keyword: `cosine`) - this is the default, combined with wordcount
* Word Count (keyword: `wordcount`) - this is the default, combined with cosine
* Byte Count (keyword: `bytecount`)
* Simhash on the raw memento content (keyword: `raw_simhash`)
* Simhash on the term frequencies of the raw memento content (keyword: `tf_simhash`)
* Jaccard Distance (keyword: `jaccard`)
* Sørensen-Dice Distance (keyword: `sorensen`)
* Latent Semantic Indexing with Gensim (keyword: `gensim_lsi`)

TimeMap measures are specified by the `-tm` argument followed by the keyword of the desired measure. Optionally, one can specify a threshold value followed by a =, like so:

`detect_off_topic -i archiveit=7877 -o outputfile.json -tm jaccard=0.80`

Multiple measures can be specified, separated by commas:

`detect_off_topic -i archiveit=7877 -o outputfile.json -tm jaccard=0.80,bytecount=-0.50`

If a threshold value is not specified the hard-coded default values are used.

## Output file formats

The output JSON file has the following format:
```
{
  "URI of a TimeMap": {
    "URI of a Memento": {
      "timemap measures": {
        "[name of measure]": {
          "comparison score": [score],
          "topic status": ["on-topic"|"off-topic"]
          }
        }
      }
    }
    ...
```

CSV output is also supported via the `-ot` option:
`detect_off_topic -i archiveit=7877 -o outputfile.csv -ot csv`

## Installing for development

To run the tests associated with the OTMT, execute:
`python ./setup.py test`

To install to run locally, run (within the base of the source directory):
`pip install .`
