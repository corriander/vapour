import { useState, useEffect } from 'react';
import Library from './Library'


const endpoint = 'http://127.0.0.1:8000/libraries/'


export default function LibrarySet (props) {

      const [libraries, setLibraries]  = useState([]);
      const final = [];

      const getLibraries = async () => {
        let response = await fetch(endpoint)
        let libraries = await response.json()
        setLibraries(libraries)
      }

      useEffect(() => {
       getLibraries()
      }, [])

      for (let library of libraries) {
        final.push(
          <Library path={library.path} size={library.size} free={library.freeBytes}/>
        )
      }

      return (
        final
      )
}

