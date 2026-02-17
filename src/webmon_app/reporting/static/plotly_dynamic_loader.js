/**
 * Plotly Dynamic Loader
 * Dynamically loads appropriate Plotly.js versions based on plot requirements
 * and handles live plot updates from a REST API endpoint
 */

const PlotlyDynamicLoader = (function() {
    'use strict';

    const loadedPlotlyScriptUrls = new Set();
    const defaultPlotlyVersion = '3.0.1';
    const plotlyBaseUrl = '/static/thirdparty/';
    const plotlyV2ScriptPath = plotlyBaseUrl + 'plotly-2.9.0.min.js';
    const plotlyV3ScriptPath = plotlyBaseUrl + 'plotly-3.0.1.min.js';
    let currentPlotHtml = '';

    function insertPlotHtml(plotHtml) {
        const graphContainer = $('#graph');
        if (graphContainer.length === 0) {
            console.error("#graph container not found in DOM for plot insertion.");
            return;
        }
        graphContainer.html(plotHtml);
        console.log("Plot HTML inserted into #graph.");
    }

    function loadPlotlyScriptAndRender(requiredVersion, plotHtmlToRender) {
        if (!requiredVersion || typeof requiredVersion !== 'string' || requiredVersion.trim() === '') {
            console.warn("Plotly version requirement is missing or invalid. Using default:", defaultPlotlyVersion);
            requiredVersion = defaultPlotlyVersion;
        }

        let scriptUrlToLoad = plotlyV2ScriptPath;
        if (requiredVersion.trim().startsWith('3.')) {
             scriptUrlToLoad = plotlyV3ScriptPath;
        }

        console.log("Plotly.js version required by plot data:", requiredVersion, "-> Mapped to script URL:", scriptUrlToLoad);

        if (loadedPlotlyScriptUrls.has(scriptUrlToLoad)) {
            console.log("Required Plotly script already loaded:", scriptUrlToLoad);
            insertPlotHtml(plotHtmlToRender);
            return;
        }

        console.log("Attempting to load Plotly.js from:", scriptUrlToLoad);
        const script = document.createElement('script');
        script.src = scriptUrlToLoad;
        script.async = false;
        script.onload = function() {
            console.log("Successfully loaded Plotly script:", scriptUrlToLoad);
            loadedPlotlyScriptUrls.add(scriptUrlToLoad);
            insertPlotHtml(plotHtmlToRender);
        };
        script.onerror = function() {
            console.error("CRITICAL ERROR: Failed to load Plotly script:", scriptUrlToLoad);
            $('#graph').html('<p class="error" style="color:red; font-weight:bold;">Error: Could not load required plotting library. Plot cannot be displayed.</p>');
        };
        document.head.appendChild(script);
    }

    function getPlotUpdate(updateUrl) {
        $.ajax({
            type: "GET",
            url: updateUrl,
            success: function(newPlotHtml) {
                if (currentPlotHtml.localeCompare(newPlotHtml) !== 0) {
                    currentPlotHtml = newPlotHtml;
                    console.log("New plot HTML received from server. Determining Plotly.js version requirement...");

                    const tempDiv = $('<div>').html(newPlotHtml);
                    const plotGraphDiv = tempDiv.find('div.plotly-graph-div');
                    let requiredVersion = null;

                    if (plotGraphDiv.length > 0 && plotGraphDiv.attr('plotlyjs-version')) {
                        requiredVersion = String(plotGraphDiv.attr('plotlyjs-version'));
                        console.log("Extracted 'plotlyjs-version' from plot div:", requiredVersion);
                    } else {
                        console.log("No 'plotlyjs-version' attribute found on the main plot div. Will use default.");
                        requiredVersion = defaultPlotlyVersion;
                    }

                    tempDiv.remove();

                    loadPlotlyScriptAndRender(requiredVersion, newPlotHtml);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error("Failed to fetch plot update from " + updateUrl + ":", textStatus, errorThrown);
                $('#graph').html('<p class="error" style="color:red;">Failed to load plot data. Please try again later.</p>');
            },
            dataType: "html",
            timeout: 25000
        });
    }

    function initializePlotUpdates(updateUrl, intervalMs) {
        if (!updateUrl) {
            console.warn("PlotlyDynamicLoader: No update URL provided, skipping initialization.");
            return;
        }

        intervalMs = intervalMs || 60000;
        getPlotUpdate(updateUrl);
        setInterval(function() {
            getPlotUpdate(updateUrl);
        }, intervalMs);
    }

    return {
        initializePlotUpdates: initializePlotUpdates,
        getPlotUpdate: getPlotUpdate
    };
})();
