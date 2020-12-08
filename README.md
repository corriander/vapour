Vapour
======

Some basic administrative tools for me to manage games libraries in bit
more of an organised manner.

Contains the following:

  - Python package for interacting with Steam libraries/games.
  - PostgreSQL DDL for scraping performance data.

Note: There's nothing in the master branch yet because it's only been
manually tested and I want to keep it clean in the event I do more
with this.


Usage
-----

### UI

    conda install nodejs
    npm install npm@latest -g

### API

	uvicorn vapour.api.main:app --reload
	http://127.0.0.1:8000/docs

### Redis & Dramatiq

Redis is used as a message broker for archive requests via the React UI.

	sudo service redis start

Dramatiq is used for worker threads responsible for handling messages posted to the queue

	dramatiq vapour.workers


### Library Management

Archiving and removing a game from the steam library to make space for
another without the need to re-download:

	conda activate gameadmin
	python
	>>> from gameadmin import steam
	>>> libs = steam.libs
	>>> print(libs[0].as_table())
	>>> game = libs[0].select('MyGame')
	>>> game.archive()
	>>> game.remove()


#### Configuration

Add a `settings.json` to `~/AppData/Local/gameadmin` or
`~/.config/gameadmin` in Linux containing something like:

	{
		"collections": {
			"archives": [
				"/path/to/archive/dir"
			]
		}
	}

### PostgreSQL Storage

#### Fraps

Used for grabbing FPS data. We only care about the frametimes.csv
output as this contains everything we need to derive the rest.

In Git Bash:

	for f in *frametimes.csv
	do
		echo "SELECT fraps.import_frames('"$(pwd | sed 's#^/\([a-zA-Z]\)#\1:#')"/$f');"
	done | psql -d gameadmin


#### GPU-Z

Pre-process and import the sensor log:

	grep -v '^\s\+Date' sensor.log | sed 's/\s*,\s*$//;s/\s*,\s*/,/g' > sensor.log.csv

	gameadmin-# SELECT gpuz.import_sensor('C:\Path\to\sensor.log.csv');


#### Performance Monitor

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


##### Pre-processing

Preprocess the binary logs in PowerShell:

	Get-ChildItem ./*/percore.blg | ForEach-Object {
		relog $_.FullName -f csv -o $("../../csv/" + $_.Directory.BaseName + "_percore.csv")
	}

Dates are in MM/DD/YYYY format in my locale; fix:

	Get-ChildItem *.csv | ForEach-Object {
		(Get-Content $_.FullName) -replace "(\d{2})\/(\d{2})\/(\d{4}) ", '$3-$1-$2T' | Set-Content $_.FullName
	}

NULLs are ' '; this also needs fixing:

	Get-ChildItem *.csv | ForEach-Object {
		(Get-Content $_.FullName) -replace '" "', '-' | Set-Content $_.FullName
	}


> Note that there is no attempt to preserve the core numbering. It's
> not envisioned this is important but if it is it should probably
> happen in the pre-processing step.


Issues
------

### `steam`

  - Archiving should remove the game from the library by default. It's
    not that sensible to treat a game as "archived" if it's remained
	in a library and since had significant updates. Removing the game
	(making it either active or inactive) sidesteps this and is
	probably the desired effect. This also avoids having to implement
	an easy way of checking whether a game is in the archive (it
	either is in there, *or* a library).

	> The only issue with this is that archiving is being used as a
	> safety net for moving games between libraries. That said,
	> libraries exist on different filesystems, so there's no
	> opportunity for a quick from lib-to-lib, but there's a
	> possibility of a quick move from lib-to-archive, or
	> archive-to-lib, as that may exist on the same filesystem...
	> (though it seems rather pointless having games archived when
	> they could be installed in a co-located library - it's just
	> ended up this way on my system).
