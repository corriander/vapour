export async function getLibraryGames(key, libraryId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/libraries/${libraryId}/games/`)
      .then(response => response.json());
}

export async function getLibraries() {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/libraries/`)
      .then(response => response.json());
}

export async function getArchives() {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/archives/`)
      .then(response => response.json());
}

export async function getArchiveGames(key, archiveId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/archives/${archiveId}/games/`)
      .then(response => response.json());
}

export async function getGame(key, appId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/games/${appId}`)
      .then(response => response.json());
}

export async function getArchivedGame(key, appId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/archived-games/${appId}`)
      .then(response => response.json());
}