import Accordion from './Accordion'
import LibraryChart from './LibraryChart'


export default function Library(props) {

    const sizeData = [];

    for (let game of props.games) {
      let sizeDatum = (({name, size}) => ({name, size}))(game);
      sizeData.push(sizeDatum);
    }

    sizeData.sort((a, b) => b.size - a.size);

    return (
      <Accordion title={props.path}>
        <LibraryChart id={props.id} data={sizeData}/>
        <p>{props.games.length} Games | {humanise(props.size)} | {humanise(props.free)} free</p>
      </Accordion>
    )
}

function humanise(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kiB', 'MiB', 'GiB', 'TiB'][i];
};