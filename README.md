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


Notes
-----

The following links have information about parsing (binary) performance
monitor log files (`*.blg`):

  - <http://stackoverflow.com/a/6248264>
  - <http://blog.bennett-scharf.com/2008/12/17/converting-an-existing-perfmon-blg-file-to-csv/>

The gist is that you can convert existing log files with **relog**
and it might be worth considering **logman** for the future as it is
capable of spooling off a format of your choice removing this
conversion step.

It's also worth noting that The Scripting Guys detail how to use
PowerShell to generate performance logs:

  - <https://blogs.technet.microsoft.com/heyscriptingguy/2011/07/29/create-and-parse-performance-monitor-logs-with-powershell/>
