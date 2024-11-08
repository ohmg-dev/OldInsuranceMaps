#! /usr/bin/bash

source .env
source ./env/bin/activate

DATETIME=`date +"%Y-%m-%d__%H%M"`
BACKUPDIR=backup
OUTDIR=$BACKUPDIR/$DATETIME

mkdir $OUTDIR

models="accounts.user
	places.place
	georeference.itembase
	georeference.sessionbase
	georeference.layersetcategory
	georeference.annotationset
	georeference.documentlink
	georeference.gcpgroup
	georeference.gcp
	loc_insurancemaps.sheet
	loc_insurancemaps.volume"

for i in $models; do
  echo dumping $i
  python manage.py dumpdata $i > $OUTDIR/$i.json
done

tar -czvf $BACKUPDIR/ohmg_$DATETIME.tar.gz $OUTDIR/*
