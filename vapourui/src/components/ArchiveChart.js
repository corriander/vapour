import React, { useEffect, useRef } from 'react';

import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

am4core.useTheme(am4themes_animated);


export default function ArchiveChart(props) {
    const chart = useRef(null);
    const divId = "bulletchartdiv-" + props.id
    const potentialSize = props.size + props.free


    useEffect(() => {
        let x = am4core.create(divId, am4charts.XYChart);

        x.paddingRight = 20;

        x.data = [{
            "category": "Archive Size",
            "value": props.size / potentialSize * 100,
            "target": props.maxSize / potentialSize * 100
        }]

        let categoryAxis = x.yAxes.push(new am4charts.CategoryAxis())
        categoryAxis.dataFields.category = "category"
        categoryAxis.renderer.minGridDistance = 30;
        categoryAxis.renderer.grid.template.disabled = true;

        let valueAxis = x.xAxes.push(new am4charts.ValueAxis())
        valueAxis.renderer.minGridDistance = 30
        valueAxis.renderer.grid.template.disabled = true
        valueAxis.min = 0;
        valueAxis.max = 100;
        valueAxis.strictMinMax = true;
        valueAxis.renderer.labels.template.adapter.add("text", function (text) {return text + "%";})

        const createRange = (axis, from, to, color) => {
            let range = axis.axisRanges.create();
            range.value = from
            range.endValue = to
            range.axisFill.fill = color;
            range.axisFill.fillOpacity = 0.8;
            range.label.disabled = true
        }

        createRange(valueAxis, 0, 20, am4core.color("#19d228"));
        createRange(valueAxis, 20, 40, am4core.color("#b4dd1e"));
        createRange(valueAxis, 40, 60, am4core.color("#f4fb16"));
        createRange(valueAxis, 60, 80, am4core.color("#f6d32b"));
        createRange(valueAxis, 80, 100, am4core.color("#fb7116"));

        let series = x.series.push(new am4charts.ColumnSeries());
        series.dataFields.valueX = "value";
        series.dataFields.categoryY = "category";
        series.columns.template.fill = am4core.color("#000");
        series.columns.template.stroke = am4core.color("#fff");
        series.columns.template.strokeWidth = 1;
        series.columns.template.strokeOpacity = 0.5;
        series.columns.template.height = am4core.percent(25);

        let series2 = x.series.push(new am4charts.LineSeries());
        series2.dataFields.valueX = "target";
        series2.dataFields.categoryY = "category";
        series2.strokeWidth = 0;

        let bullet = series2.bullets.push(new am4charts.Bullet());
        let line = bullet.createChild(am4core.Line);
        line.x1 = 0;
        line.y1 = -80;
        line.x2 = 0;
        line.y2 = 80;
        line.stroke = am4core.color("#000");
        line.strokeWidth = 4;

        chart.current = x;

        return () => {
            x.dispose();
        };
    }, [props.data, divId, props.free, props.threshold]);

    // When the paddingRight prop changes the chart will update
    useEffect(() => {
        chart.current.paddingRight = props.paddingRight;
    }, [props.paddingRight]);

    return (
        <div id={divId} style={{ width: "100%", height: "500px" }}></div>
    );
}

