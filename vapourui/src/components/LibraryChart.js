import React, { useEffect, useRef } from 'react';

import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

am4core.useTheme(am4themes_animated);


export default function LibraryChart(props) {
    const chart = useRef(null);
    const divId = "piechartdiv-" + props.id


    useEffect(() => {
        const freeSlice = {name: "Remaining", size: props.free}

        let x = am4core.create(divId, am4charts.PieChart);

        x.paddingRight = 20;

        // Two-level pie chart https://www.amcharts.com/demos/two-level-pie-chart/
        x.innerRadius = am4core.percent(30);

        // Add data -- added to series explicitly now
        //x.data = props.data
        let sizeData = [...props.data].sort((a,b) => b.size - a.size);

        // Add and configure background Series
        let fgSeries = x.series.push(new am4charts.PieSeries());
        fgSeries.dataFields.value = "size";
        fgSeries.dataFields.category = "name";
        fgSeries.slices.template.stroke = am4core.color("#fff");
        fgSeries.innerRadius = 10;
        fgSeries.slices.template.fillOpacity = 0.6;
        fgSeries.slices.template.tooltipPosition = "pointer";

        fgSeries.slices.template.propertyFields.disabled = "labelDisabled";
        fgSeries.slices.template.propertyFields.isActive = "hasFocus";
        //fgSeries.labels.template.propertyFields.disabled = "labelDisabled";
        fgSeries.ticks.template.propertyFields.disabled = "labelDisabled";
        fgSeries.labels.template.disabled = true;

        // Set data (including missing slice)
        let missingSlice = { ...freeSlice };
        missingSlice.labelDisabled = true;
        fgSeries.data = [...sizeData];
        fgSeries.data.push(missingSlice);

        fgSeries.adapter.add("innerRadius", function(innerRadius, target){
            return am4core.percent(20);
        })
        fgSeries.adapter.add("radius", function(innerRadius, target){
            return am4core.percent(100);
        })


        let bgSeries = x.series.push(new am4charts.PieSeries());
        bgSeries.dataFields.value = "size";
        bgSeries.dataFields.category = "name";
        bgSeries.slices.template.propertyFields.fill = "fill";
        bgSeries.slices.template.tooltipPosition = "pointer";
        bgSeries.slices.template.states.getKey("active").properties.shiftRadius = 0;
        //bgSeries.alignLabels = false;

        // Set data (including remaining disk space)
        let remainingSlice = { ...freeSlice };
        remainingSlice.fill = "#dedede";
        //remainingSlice.labelDisabled = false;
        bgSeries.data = [...sizeData];
        //bgSeries.data.forEach(slice => slice.labelDisabled = true)
        bgSeries.data.push(remainingSlice);

        // Disable poppping out of slices on background series
        bgSeries.slices.template.states.getKey("hover").properties.shiftRadius = 0;
        bgSeries.slices.template.states.getKey("hover").properties.scale = 1;

        bgSeries.adapter.add("innerRadius", function(innerRadius, target){
            return am4core.percent(20);
        })
        bgSeries.adapter.add("radius", function(innerRadius, target){
            return am4core.percent(40);
        })

        fgSeries.slices.template.events.on("hit", function(e) {
            let series = e.target.dataItem.component;
            series.slices.each(function(item) {
                if (item.isActive && item !== e.target) {
                    item.isActive = false;
                }
            })
            props.selectHandler(e.target.dataItem.dataContext.id)
        });

        bgSeries.labels.events.on("ready", labelsReady);

        function labelsReady(ev) {
            console.log("I'm here");
        }

        bgSeries.ticks.template.events.on("ready", hideSmall);
        bgSeries.ticks.template.events.on("visibilitychanged", hideSmall);
        bgSeries.labels.template.events.on("ready", hideSmall);
        bgSeries.labels.template.events.on("visibilitychanged", hideSmall);

        function hideSmall(ev) {
            if (ev.target.dataItem && (ev.target.dataItem.values.value.percent < props.threshold)) {
              ev.target.hide()
            }
            else {
               ev.target.show();
            }
        }

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

