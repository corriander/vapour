import { useState } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { useQuery } from "react-query";
import { getGame, getArchivedGame } from "../services/libraryService";
import GameTable from "./GameTable";
import ArchiveButton from './ArchiveButton';

function getModalStyle() {
  return {
    top: '50%',
    left: '10%'
  };
}

const useStyles = makeStyles((theme) => ({
  paper: {
    position: 'absolute',
    width: '80%',
    backgroundColor: theme.palette.background.paper,
    border: '2px solid #000',
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 3),
    outline: 0
  },
  imageContainer: {
    display: 'flex',
    justifyContent: 'center'
  },
  image: {
    maxWidth: '100%',
    height: 'auto',
  },
}))

export default function GameModal (props) {
      const getQueryFunc = () => {
        switch (props.gameType) {
            case 'game':
              return getGame
            case 'archivedgame':
              return getArchivedGame
            default:
              console.log(`${props.gameType} is an unrecognised type; should be in {game, archivedgame}`)
        }
      }
      const { data, isLoading, error } = useQuery([props.gameType, props.id], getQueryFunc());

      const classes = useStyles();
      const [modalStyle] = useState(getModalStyle);

      if (isLoading) return "Loading...";
      if (error) return "Oops!";

      return (
        <div style={modalStyle} className={classes.paper}>
            <h2 id="game-modal-title">{data.name}</h2>
            <div className={classes.imageContainer}>
              <a href={data.storeUrl}>
                  <img className={classes.image} alt={data.name} src={data.imgUrl}/>
              </a>
            </div>
            <GameTable id={props.id} manifestPath={data.manifestPath} installPath={data.installPath} size={data.size}/>
            <ArchiveButton appId={props.id} archiveId={1} gameType={props.gameType}/>
        </div>
      )

}

