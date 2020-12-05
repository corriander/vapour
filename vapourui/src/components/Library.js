import React from 'react';
import Accordion from './Accordion'
import LibraryChart from './LibraryChart'
import LibraryTable from './LibraryTable'

import { useQuery } from 'react-query';
import { getGames } from '../services/libraryService';


export default function Library(props) {
    const { data: games, isLoading } = useQuery(["librarygames", props.id], getGames);

    // Prepare data for components
    const gebify = x => (x / Math.pow(1024, 3)).toFixed(2);
    const threshold = 10e9 / (props.size + props.free) * 100;
    // THANK YOU https://www.reddit.com/r/reactjs/comments/jjz93y/how_do_i_use_reactquery_to_join_data_from/
    // This was driving me mad - would only work on a hot update without the conditional in there to prevent
    // a compile failure because games doesn't exist when we try to .map
    const humanisedGames = React.useMemo(() => {
      return isLoading ? [] : games.map(obj => ({ ...obj, size: gebify(obj.size) }))
    }, [games]);


    return (
      <Accordion title={props.path}>
        <LibraryChart id={props.id} free={gebify(props.free)} threshold={threshold} data={humanisedGames}/>
        <LibraryTable libraryId={props.id} data={humanisedGames}/>
      </Accordion>
    )
}

function humanise(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kiB', 'MiB', 'GiB', 'TiB'][i];
};