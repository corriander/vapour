import React, { useState, useEffect } from 'react';
import Modal from '@material-ui/core/Modal';
import Accordion from './Accordion'
import LibraryChart from './LibraryChart'
import LibraryTable from './LibraryTable'
import GameModal from './GameModal'

import { useQuery } from 'react-query';
import { getGames } from '../services/libraryService';


export default function Library(props) {
    const { data: games, isLoading } = useQuery(["librarygames", props.id], getGames);
    const [ focus, setFocus ] = useState(null);
    const [ data, setData ] = useState([]);

    // Prepare data for components
    const gebify = x => (x / Math.pow(1024, 3)).toFixed(2);
    const threshold = 10e9 / (props.size + props.free) * 100;
    // THANK YOU https://www.reddit.com/r/reactjs/comments/jjz93y/how_do_i_use_reactquery_to_join_data_from/
    // This was driving me mad - would only work on a hot update without the conditional in there to prevent
    // a compile failure because games doesn't exist when we try to .map
    const humanisedGames = React.useMemo(() => {
      return isLoading ? [] : games.map(obj => ({ ...obj, size: gebify(obj.size) }))
    }, [games, isLoading]);

    useEffect(() => {
      setData(humanisedGames.map(obj => ({ ...obj, hasFocus: false})))
    }, [humanisedGames, focus])

    useEffect(() => {
      setData(humanisedGames.map(game => ({ ...game, hasFocus: (game.id == focus)})))
    }, [focus, humanisedGames])

    return (
      <Accordion title={props.path}>
        <LibraryChart id={props.id} free={gebify(props.free)} threshold={threshold} data={data} selectHandler={setFocus}/>
        <LibraryTable libraryId={props.id} data={data} selectHandler={setFocus}/>
        <Modal
          open={focus !== null}
          onClose={() => setFocus(null)}
          aria-labelledby="game-modal-title"
          aria-describedby="game-modal-description"
        >
          <div>
            <GameModal id={focus}/>
          </div>
        </Modal>
      </Accordion>
    )
}
