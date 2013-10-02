#!/bin/sh 
java -Xmx4g -cp FANSE-0.2.2/fanseparser-0.2.2.jar tratz.parse.ui.ParserGui data/data/wordnet3/ data/posTaggingModel.gz data/parseModel.gz
