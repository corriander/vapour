import React from 'react';
import { useSortBy, useTable, useRowSelect } from 'react-table';
import CssBaseline from '@material-ui/core/CssBaseline'
import { makeStyles } from '@material-ui/core/styles';
import Paper from "@material-ui/core/Paper"
import TableContainer from "@material-ui/core/TableContainer"
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
    minWidth: 500,
  },
  headercell: {
    fontWeight: 700,
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

// See https://stackoverflow.com/a/64489401 for alternative styling approach

export default function LibraryTable({ columns, data }) {
    const classes = useStyles();

    const tableInstance = useTable({ columns, data }, useSortBy, useRowSelect);
    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = tableInstance

    return (
      <div className={classes.root}>
        <CssBaseline/>
        <Paper className={classes.paper}>
          <TableContainer>
          <Table {...getTableProps()} className={classes.table}>
              <TableHead>
                  {// loop over the header rows
                  headerGroups.map(headerGroup => (
                    // apply the header row props
                    <TableRow {...headerGroup.getHeaderGroupProps()}>
                      {// loop over the headers in each row
                      headerGroup.headers.map(column =>(
                        // apply the header cell props
                        <TableCell className={classes.headercell}
                          {...column.getHeaderProps(column.getSortByToggleProps())}
                          align={column.isNumeric ? 'right' : 'left'}
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
                      <TableRow
                        {...row.getRowProps()}
                        hover
                        onClick={() => row.toggleRowSelected(!row.isSelected)}
                      >
                         {// loop over the cells
                         row.cells.map(cell => {
                            return (
                               <TableCell
                                 {...cell.getCellProps()}
                                 align={cell.column.isNumeric ? 'right' : 'left' }
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
          </TableContainer>
        </Paper>
      </div>
    );
}

