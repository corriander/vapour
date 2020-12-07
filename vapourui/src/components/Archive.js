import React, { useState, useEffect } from 'react';
import Modal from '@material-ui/core/Modal';
import Accordion from './Accordion'
import ArchiveChart from './ArchiveChart'
import LibraryTable from './LibraryTable'
import GameModal from './GameModal'

import { useQuery } from 'react-query';
import { getArchiveGames } from '../services/libraryService';


export default function Archive(props) {
    const { data: games, isLoading } = useQuery(["archivegames", props.id], getArchiveGames);
    const [ focus, setFocus ] = useState(null);

    // Prepare data for components
    const gebify = x => (x / Math.pow(1024, 3)).toFixed(2);
    // THANK YOU https://www.reddit.com/r/reactjs/comments/jjz93y/how_do_i_use_reactquery_to_join_data_from/
    // This was driving me mad - would only work on a hot update without the conditional in there to prevent
    // a compile failure because games doesn't exist when we try to .map
    const humanisedGames = React.useMemo(() => {
      return isLoading ? [] : games.map(obj => ({ ...obj, size: gebify(obj.size) }))
    }, [games, isLoading]);

    const title = <span><i className="fas fa-archive"></i>  {props.path}</span>

    return (
      <Accordion title={title}>
        <ArchiveChart id={props.id} size={props.size} free={props.free} maxSize={props.maxSize}/>
        <LibraryTable libraryId={props.id} data={humanisedGames} selectHandler={setFocus}/>
        <Modal
          open={focus !== null}
          onClose={() => setFocus(null)}
          aria-labelledby="game-modal-title"
          aria-describedby="game-modal-description"
        >
          <div>
            <GameModal id={focus} gameType="archivedgame"/>
          </div>
        </Modal>
      </Accordion>
    )
}
