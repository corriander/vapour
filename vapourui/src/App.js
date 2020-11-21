import './App.css';
import LibrarySet from './components/LibrarySet'
import * as am4core from "@amcharts/amcharts4/core";
import * as am4charts from "@amcharts/amcharts4/charts";
import am4themes_animated from "@amcharts/amcharts4/themes/animated";

am4core.useTheme(am4themes_animated);

function App() {
  return (
    <LibrarySet />
  );
}

export default App;
