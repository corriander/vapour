import { useQuery } from "react-query";
import { getLibraries } from "../services/libraryService";

import Library from './Library'


export default function LibrarySet (props) {
      const { data, isLoading, error } = useQuery("libraries", getLibraries);

      const final = [];

      if (isLoading) return "Loading...";
      if (error) return "Oops!";

      for (let library of data) {
        final.push(
          <Library id={library.id} path={library.path} size={library.size} free={library.freeBytes}/>
        )
      }

      return (
        final
      )
}

