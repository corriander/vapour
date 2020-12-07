import { useQuery } from "react-query";
import { getLibraries, getArchives } from "../services/libraryService";

import Library from './Library'
import Archive from './Archive'


export default function LibrarySet (props) {
      const { data: libraries, isLoading: librariesLoading, error: librariesError } = useQuery("libraries", getLibraries);
      const { data: archives, isLoading: archivesLoading, error: archivesError } = useQuery("archives", getArchives);

      const final = [];

      if (librariesLoading || archivesLoading) return "Loading...";

      if (!librariesError) {
        for (let library of libraries) {
          final.push(
            <Library id={library.id} path={library.path} size={library.size} free={library.freeBytes}/>
          )
        }
      } else {
        console.error("Error loading libraries")
      }

      if (!archivesError) {
        for (let archive of archives) {
          final.push(
            <Archive id={archive.id} path={archive.path} size={archive.size} free={archive.freeBytes} maxSize={archive.maxSize}/>
          )
        }
      } else {
        console.error("Error loading archives")
      }

      return (
        final
      )
}

