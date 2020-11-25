import React, { useState, useEffect } from 'react';
import { useSortBy, useTable } from 'react-table';


export default function LibraryTable({ columns, data }) {

    const tableInstance = useTable({ columns, data }, useSortBy);
    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = tableInstance

    return (
        <table {...getTableProps()} style={{ border: 'solid 1px blue'}}>
            <thead>
                {// loop over the header rows
                headerGroups.map(headerGroup => (
                  // apply the header row props
                  <tr {...headerGroup.getHeaderGroupProps()}>
                    {// loop over the headers in each row
                    headerGroup.headers.map(column =>(
                      // apply the header cell props
                      <th
                        {...column.getHeaderProps(column.getSortByToggleProps())}
                        style={{
                            borderBottom: 'solid 3px red',
                            background: 'aliceblue',
                            color: 'black',
                            fontWeight: 'bold',
                        }}
                        >
                        {// render the header
                        column.render('Header')}
                        <span>
                          {column.isSorted
                            ? column.isSortedDesc
                              ? ' 🔽'
                              : ' 🔼'
                            : ''}
                        </span>
                      </th>
                    ))}
                  </tr>
                ))}
            </thead>
            {/* apply the table body props */}
            <tbody {...getTableBodyProps()}>
                {// loop over the table rows
                rows.map((row, i) => {
                  // prepare the row for display
                  prepareRow(row)
                  return (
                    // apply the row propers
                    <tr {...row.getRowProps()}>
                       {// loop over the cells
                       row.cells.map(cell => {
                          return (
                             <td
                               {...cell.getCellProps()}
                               style={{
                                   padding: '10px',
                                   border: 'solid 1px gray',
                                   background: 'papayawhip',
                               }}
                             >
                                 {// render the cell contents
                                 cell.render('Cell')}
                             </td>
                          )
                    })}
                </tr>
                  )
                })}
            </tbody>
        </table>
    );
}

