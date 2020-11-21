import React, { useRef, useLayoutEffect } from 'react';

import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

am4core.useTheme(am4themes_animated);


export default function LibraryChart(props) {
    const chart = useRef(null);
    const divId = "chartdiv-" + props.id

    useLayoutEffect(() => {
        let x = am4core.create(divId, am4charts.PieChart);

        x.paddingRight = 20;

        // Add data
        x.data = props.data

        // Add and configure Series
        let pieSeries = x.series.push(new am4charts.PieSeries());
        pieSeries.dataFields.value = "size";
        pieSeries.dataFields.category = "name";
        // ...
        chart.current = x;

        return () => {
            x.dispose();
        };
    }, []);

    // When the paddingRight prop changes the chart will update
    useLayoutEffect(() => {
        chart.current.paddingRight = props.paddingRight;
    }, [props.paddingRight]);

    return (
        <div id={divId} style={{ width: "100%", height: "300px" }}></div>
    );
}

