import React, { useState, useEffect } from 'react';
import { useSortBy, useTable } from 'react-table';
import { makeStyles } from '@material-ui/core/styles';
import Paper from "@material-ui/core/Paper"
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import TableSortLabel from "@material-ui/core/TableSortLabel";

const useStyles = makeStyles((theme) => ({
  root: {
    width: '100%',
  },
  paper: {
    width: '100%',
    marginBottom: theme.spacing(2),
  },
  table: {
    minWidth: 750,
  },
  visuallyHidden: {
    border: 0,
    clip: 'rect(0 0 0 0)',
    height: 1,
    margin: -1,
    overflow: 'hidden',
    padding: 0,
    position: 'absolute',
    top: 20,
    width: 1,
  },
}));

export default function LibraryTable({ columns, data }) {
    const classes = useStyles();

    const tableInstance = useTable({ columns, data }, useSortBy);
    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = tableInstance

    return (
        <Paper className={classes.paper}>
          <Table {...getTableProps()}>
              <TableHead>
                  {// loop over the header rows
                  headerGroups.map(headerGroup => (
                    // apply the header row props
                    <TableRow {...headerGroup.getHeaderGroupProps()}>
                      {// loop over the headers in each row
                      headerGroup.headers.map(column =>(
                        // apply the header cell props
                        <TableCell
                          {...column.getHeaderProps(column.getSortByToggleProps())}
                          >
                            <TableSortLabel
                              active={column.isSorted}
                              direction={column.isSortedDesc ? 'desc' : 'asc'}
                            >
                              {column.render('Header')}
                              {column.isSorted ? (
                                <span className={classes.visuallyHidden}>
                                  {column.isSortedDesc ? 'sorted descending' : 'sorted ascending'}
                                </span>
                              ) : null}
                            </TableSortLabel>
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
              </TableHead>
              {/* apply the table body props */}
              <TableBody {...getTableBodyProps()}>
                  {// loop over the table rows
                  rows.map((row, i) => {
                    // prepare the row for display
                    prepareRow(row)
                    return (
                      // apply the row propers
                      <TableRow {...row.getRowProps()}>
                         {// loop over the cells
                         row.cells.map(cell => {
                            return (
                               <TableCell
                                 {...cell.getCellProps()}
                               >
                                   {// render the cell contents
                                   cell.render('Cell')}
                               </TableCell>
                            )
                      })}
                  </TableRow>
                    )
                  })}
              </TableBody>
          </Table>
        </Paper>
    );
}

