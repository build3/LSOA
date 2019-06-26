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
    $('#slider-value').html(`Observations from: ${formatDate($('#date-slider').slider("option", "min"))}
        to: ${formatDate(dateToTime(window.maxDate))}`);

    /**
     * Changes element which displays current date. Called when moving slider.
     */
    function slide(event, ui) {
        $("#slider-value").html(`Observations from: ${(formatDate(ui.value))}
            to: ${formatDate(dateToTime(window.maxDate))}`);
    }

    /**
     * Function called when value in slider change.
     * Filters observations by current date on slider.
     */
    function change(event, ui) {
        const timestamp = dateToTime(ui.value);

        var observationsFiltered = {};
        var allStars = {};
        Object.keys(observations).forEach(construct => allStars[construct] = 0);

        for (var construct in observations) {
            observationsFiltered[construct] = {};

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
                    const size = observationsFiltered[construct][course][sublevel].length;
                    const color = calculateNewColor(size, allStars[construct]);

                    let elem = $(`.star-chart-4-table-${construct}`)
                        .find(`.heat-${course}-${sublevel}`)
                        .attr('bgcolor', color);

                    elem[0].dataset.color = color;

                    $(`.star-chart-4-table-${construct}`)
                        .find(`.stars-${course}-${sublevel}`)
                        .html(size);
                }
            }
        }
    }

    /**
     * Calculates new color when value in slider change. To get new color for level
     * new percent value is calculated. When starAmount is 0 color for 0% is used.
     * When starAmount is equal to allStars which are inside table then color with `10` key is returned.
     * If new `percentValue` is less than 10% `LESS_THEN_10` key is used.
     * Otherwise color is taken from the first digit from new `percentValue`. For example when
     * `percentValue` is 73% the first digit is 7 and `7` key is used to get value from `COLORS_DARK` dict.
     * @param {Integer} starAmount 
     * @param {Integer} allStars 
     */
    function calculateNewColor(starAmount, allStars) {
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
