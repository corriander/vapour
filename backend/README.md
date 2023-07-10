Vapour API
===

Python modules for interacting with Steam libraries and games with an API


## Usage

### API

    poetry run api

See <http://127.0.0.1:8000/docs`>

### Redis & Dramatiq

Redis is used as a message broker for archive requests via the React UI.

	sudo service redis-server start

Dramatiq is used for worker threads responsible for handling messages posted to the queue

	dramatiq vapour.workers

### Direct

#### Archiving

    conda activate gameadmin
    python
    >>> from gameadmin import steam
    >>> libs = steam.libs
    >>> print(libs[0].as_table())
    >>> game = libs[0].select('MyGame')
    >>> game.archive()
    >>> game.remove()


### Configuration

Add a `settings.json` to `~/AppData/Local/vapour` or
`~/.config/vapour` in Linux containing something like:

	{
		"collections": {
			"archives": [
				"/path/to/archive/dir"
			]
		}
	}

