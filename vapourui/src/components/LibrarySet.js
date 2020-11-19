import { useState, useEffect } from 'react';
import logo from '../logo.svg'
import Accordion from './Accordion'


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
          <Accordion title={library.path}>
            <img src={logo} className="App-logo" alt="logo" />

             Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.
          </Accordion>
        )
      }

      return (
        final
      )
}

