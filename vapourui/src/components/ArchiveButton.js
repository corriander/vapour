import React, { useState } from 'react';
import Button from '@material-ui/core/Button';

export default function ArchiveButton (props) {
    const [enabled, setEnabled] = useState(props.gameType === 'game')

    const handleClick = () => {
        setEnabled(false)
        fetch(`${process.env.REACT_APP_API_BASE_URL}/archives/${props.archiveId}/games/${props.appId}`, {
            method: 'PUT'
        })
    }

    return (
        <Button
            variant="contained"
            {...(enabled ? {color: "primary"} : {disabled: true})}
            onClick={handleClick}
        >
        Archive
        </Button>
    )
}
