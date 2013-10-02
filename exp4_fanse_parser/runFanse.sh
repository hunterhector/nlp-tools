#!/bin/sh 

#not finished yet
java -cp FANSE-0.2.2/fanseparser-0.2.2.jar tratz.parse.ParsingScript -input ../exp1/cleaned/ -posmodel data/posTaggingModel.gz -parsemodel data/parseModel.gz -possmodel data/possessivesModel.gz -nnmodel data/nnModel.gz -psdmodel data/psdModels.gz -srlargsmodel data/srlArgsWrapper.gz -wndir data/data/wordnet3/
