import { useQuery } from "react-query";
import { getLibraries, getArchives } from "../services/libraryService";

import Library from './Library'
import Archive from './Archive'


export default function LibrarySet (props) {
      const { data: libraries, isLoading: librariesLoading, error: librariesError } = useQuery("libraries", getLibraries);
      const { data: archives, isLoading: archivesLoading, error: archivesError } = useQuery("archives", getArchives);

      const archiveElements = [];
      const libraryElements = [];

      const final = [];

      if (librariesLoading || archivesLoading) return "Loading...";
      if (archivesError) return "Error loading archives"
      if (librariesError) return "Error loading libraries"

      for (let library of libraries) {
        final.push(
          <Library id={library.id} path={library.path} size={library.size} free={library.freeBytes}/>
        )
      }

      for (let archive of archives) {
        final.push(
          <Archive id={archive.id} path={archive.path} size={archive.size} free={archive.freeBytes} maxSize={archive.maxSize}/>
        )
      }

      return (
        final
      )
}

