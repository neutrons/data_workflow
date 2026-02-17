/**
 * Plot Initialization
 * Reads plot configuration from JSON script tag and initializes dynamic plot updates
 */

(function() {
    'use strict';

    function getJsonScriptData(elementId) {
        var element = document.getElementById(elementId);
        if (element) {
            return JSON.parse(element.textContent);
        }
        return null;
    }

    var updateUrl = getJsonScriptData('plot-update-url');
    if (updateUrl) {
        PlotlyDynamicLoader.initializePlotUpdates(updateUrl, 60000);
    }
})();
