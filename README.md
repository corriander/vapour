Some basic administrative tools for me to manage games libraries in bit
more of an organised manner.

Contains the following:

  - Python Module for interacting with Steam libraries/games so far.
  - PostgreSQL DDL for scraping performance data.

Note: There's nothing in the master branch yet because it's only been
manually tested and I want to keep it clean in the event I do more
with this.


Usage
-----

### PostgreSQL Storage

#### Fraps

Used for grabbing FPS data. We only care about the frametimes.csv
output as this contains everything we need to derive the rest.

In Git Bash:

	for f in *frametimes.csv
	do 
		echo "SELECT fraps.import_frames('$(pwd)/$f');" | sed 's#^/\([a-zA-Z]\)#\1:#'
	done | psql -d gameadmin


#### GPU-Z

Pre-process and import the sensor log:

	grep -v '^\s\+Date' sensor.log | sed 's/\s*,\s*$//;s/\s*,\s*/,/g' > sensor.log.csv

	gameadmin-# SELECT gpuz.import_sensor('C:\Path\to\sensor.log.csv');

