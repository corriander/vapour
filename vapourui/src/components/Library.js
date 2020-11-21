import logo from '../logo.svg'
import Accordion from './Accordion'


export default function Library(props) {
    return (
      <Accordion title={props.path}>
        <img src={logo} className="App-logo" alt="logo" />
        <p>{props.games.length} Games | {humanise(props.size)} | {humanise(props.free)} free</p>
      </Accordion>
    )
}

function humanise(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kiB', 'MiB', 'GiB', 'TiB'][i];
};