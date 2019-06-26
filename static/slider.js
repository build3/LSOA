/**
 * This file contains all logic for slider in star chart v4.
 * 
 * Description of changing cells when moving slider:
 * 
 * 1. First parse `observations` from context. Parsed dict will looks like this:
 * {
 *   constructID: {
 *     classID: {
 *         sublevelID: [Array with timestamps from `observation_date`]
 *     }
 *   }
 * }
 * 
 * 2. When sliding change value current displayed date.
 * 
 * 3. When value in slider change, filter parsed `observation` using current
 *   date from slider comparing two timestamps. In addition calculate new quantity of
 *   filtered observations.
 * 
 * 4. Use filtered observations and new quantity of observations to calculate new color for cell.
 * 
 * 5. Change color in cells and value below them.
 * 
 */

(() => {
    const observations = JSON.parse(window.observations) || {};
    const COLORS_DARK = JSON.parse(window.COLORS_DARK)

    $('#date-slider').slider({
        min: dateToTime(window.minDate),
        max: dateToTime(window.maxDate),
        change: change,
        slide: slide
    });

    // Set start value to min date available in slider.
    $('#slider-value').html(`Current date: ${formatDate($('#date-slider').slider("option", "min"))}`);

    /**
     * Changes element which displays current date. Called when moving slider.
     */
    function slide(event, ui) {
        $("#slider-value").html(`Current date: ${(formatDate(ui.value))}`);
    }

    /**
     * Function called when value in slider change.
     * Filters observations by current date on slider.
     */
    function change(event, ui) {
        const timestamp = dateToTime(ui.value);

        var observationsFiltered = {};
        var allStars = {};

        for (var construct in observations) {
            observationsFiltered[construct] = {};

            if (!allStars.hasOwnProperty(construct)) {
                allStars[construct] = 0;
            }

            for (var course in observations[construct]) {
                observationsFiltered[construct][course] = {}

                for (var sublevel in observations[construct][course]) {
                    observationsFiltered[construct][course][sublevel] = observations[construct][course][sublevel]
                        .filter(date => dateToTime(date) > timestamp);

                    allStars[construct] += observationsFiltered[construct][course][sublevel].length;
                }
            }
        }

        changeElements(observationsFiltered, allStars);
    }

    /**
     * Changes colored cells and those with observations count after filtering observations by date.
     * @param {Object} observationsFiltered - Observations filtered by date.
     * @param {Object} allStars - Observations count per construct.
     */
    function changeElements(observationsFiltered, allStars) {
        for (var construct in observationsFiltered) {
            for (var course in observationsFiltered[construct]) {
                for (var sublevel in observationsFiltered[construct][course]) {
                    const color = calculateNewColor4(
                        observationsFiltered[construct][course][sublevel].length,
                        allStars[construct]
                    );

                    let elem = $(`.star-chart-4-table-${construct}`)
                        .find(`.heat-${course}-${sublevel}`)
                        .attr('bgcolor', color);

                    elem[0].dataset.color = color;

                    $(`.star-chart-4-table-${construct}`)
                        .find(`.stars-${course}-${sublevel}`)
                        .html(observationsFiltered[construct][course][sublevel].length);
                }
            }
        }
    }

    /**
     * Calculates new color for merged level. To get new color for level
     * new percent value is calculated. When starAmount is 0 color for 0% is used.
     * When starAmount is equal to allStars which are inside table then color with `10` key is returned.
     * If new `percentValue` is less than 10% `LESS_THEN_10` key is used.
     * Otherwise color is taken from the first digit from new `percentValue`. For example when
     * `percentValue` is 73% the first digit is 7 and `7` key is used to get value from `COLORS_DARK` dict.
     * @param {Integer} starAmount 
     * @param {Integer} constructId 
     */
    function calculateNewColor4(starAmount, allStars) {
        if (starAmount == 0) {
            return COLORS_DARK["0"];
        }

        if (starAmount == allStars) {
            return COLORS_DARK["10"];
        }

        const percentValue = 100 * starAmount / allStars;

        if (percentValue < 10) {
            return COLORS_DARK["LESS_THEN_10"]
        } else {
            return COLORS_DARK[percentValue.toString()[0]]
        }
    }

    /**
     * Create and format date to display from time in milliseconds.
     * @param {Number} value - Time in millis.
     */
    function formatDate(value) {
        let options = {"month": "long", "day": "2-digit", "year": "numeric"};
        return new Date(value * 1000).toLocaleDateString("en-US", options);
    }

    function dateToTime(date) {
        return new Date(date).getTime() / 1000;
    }
})()
