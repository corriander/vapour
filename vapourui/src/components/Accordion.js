import { useState } from 'react';

export default function Accordion(props) {
    const [expand, setExpand] = useState(props.isExpand);
    return (
      <div className="box">
        <div className="title-box" onClick={() => setExpand(expand => !expand)}>
          <span className="title">{props.title}</span>
          <span className="icon"><i className={`fa fa-play-circle${!expand ? ' down' : ''}`}></i></span>
          <div className="clearfix"></div>
        </div>
        {expand && <div className="content">{props.children}</div>}
      </div>
    )
}