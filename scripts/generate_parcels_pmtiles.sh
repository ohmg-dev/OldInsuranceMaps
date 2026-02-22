#! /usr/bin/bash

## SCRIPT MIGRATED FOR REFERENCE FEB 18, 2026

infile=$1
outfile=$2
nocache=$3
basepath="${infile%.*}"
intpath=$basepath".geojson"
filename="$(basename $basepath)"

echo "in file: "$infile
echo "intermediate file: "$intpath
echo "output file: "$outfile

inext="${infile##*.}"

if [[ $nocache == "--no-cache" ]] && [[ -f $intpath ]] && [[ ! inext == "geojson" ]]; then
	rm $intpath
fi

if [[ ! -f $intpath ]] && [[ ! inext == "geojson" ]]; then
	SECONDS=0
	duration=$SECONDS
	echo "$((duration / 60)) minutes and $((duration % 60)) seconds elapsed."
	echo "creating GeoJSON file..."
	ogr2ogr -of geojson -select "" -t_srs "EPSG:4326" $intpath $infile
else
	echo "GeoJSON file already exists (or was initial input)"
fi

SECONDS=0

tippecanoe \
	-z15 -Z10 \
	--no-simplification-of-shared-nodes \
	--coalesce-densest-as-needed \
	--extend-zooms-if-still-dropping \
	-o $outfile \
	--force $intpath

echo $outfile" created"

duration=$SECONDS
echo "$((duration / 60)) minutes and $((duration % 60)) seconds elapsed."
