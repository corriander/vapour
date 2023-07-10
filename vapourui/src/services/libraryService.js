export async function getLibraryGames(key, libraryId) {
  return fetch(`/libraries/${libraryId}/games/`)
      .then(response => response.json());
}

export async function getLibraries() {
  return fetch(`/libraries/`)
      .then(response => response.json());
}

export async function getArchives() {
  return fetch(`/archives/`)
      .then(response => response.json());
}

export async function getArchiveGames(key, archiveId) {
  return fetch(`/archives/${archiveId}/games/`)
      .then(response => response.json());
}

export async function getGame(key, appId) {
  return fetch(`/games/${appId}`)
      .then(response => response.json());
}

export async function getArchivedGame(key, appId) {
  return fetch(`/archived-games/${appId}`)
      .then(response => response.json());
}
