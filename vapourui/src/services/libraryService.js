export async function getGames(key, libraryId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/libraries/${libraryId}/games/`)
      .then(response => response.json());
}

export async function getLibraries() {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/libraries/`)
      .then(response => response.json());
}

export async function getGame(key, appId) {
    return fetch(`${process.env.REACT_APP_API_BASE_URL}/games/${appId}`)
      .then(response => response.json());
}