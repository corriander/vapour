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

      //const disabled_archive_button = <Button variant="contained" disabled>
      //    Archive
      //  </Button>
      //const archive_button = <Button variant="contained" color="primary" href={`${process.env.REACT_APP_API_BASE_URL}/archives/1/games/${props.id}`}>
      //    Archive
      //  </Button>

      return (
        <div style={modalStyle} className={classes.paper}>
            <h2 id="game-modal-title">{data.name}</h2>
            <div className={classes.imageContainer}>
              <a href={data.storeUrl}>
                  <img className={classes.image} alt={data.name} src={data.imgUrl}/>
              </a>
            </div>
            <GameTable id={props.id} manifestPath={data.manifestPath} installPath={data.installPath} size={data.size}/>
            {/*props.gameType === 'game' ? archive_button : disabled_archive_button*/}
            <ArchiveButton appId={props.id} archiveId={0} gameType={props.gameType}/>
        </div>
      )

}

