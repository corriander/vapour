import Accordion from './Accordion'
import LibraryChart from './LibraryChart'

import { useQuery } from 'react-query';
import { getGames } from '../services/libraryService';


export default function Library(props) {
    const { data: games, isLoading, error } = useQuery(["librarygames", props.id], getGames);

    // Prepare data for LibraryChart
    const threshold = 10e9 / (props.size + props.free) * 100;

    return (
      <Accordion title={props.path}>
        <LibraryChart id={props.id} free={props.free} threshold={threshold} data={games}/>
      </Accordion>
    )
}

function humanise(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kiB', 'MiB', 'GiB', 'TiB'][i];
};