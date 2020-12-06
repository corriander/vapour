import { useQuery } from "react-query";
import { makeStyles } from '@material-ui/core/styles';
import { getGame } from "../services/libraryService";

const useStyles = makeStyles((theme) => ({
  table: {
    th: {
      alignText: 'right'
    }
  }
}))

function humanise(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kiB', 'MiB', 'GiB', 'TiB'][i];
};

export default function GameTable (props) {
  const classes = useStyles();

  return (
    <table className={classes.table}>
      <tbody>
      <tr><th>AppID</th><td>{props.id}</td></tr>
        <tr><th>Manifest</th><td>{props.manifestPath}</td></tr>
        <tr><th>Install</th><td>{props.installPath}</td></tr>
        <tr><th>Size</th><td>{humanise(props.size)}</td></tr>
      </tbody>
     </table>
  )
}
