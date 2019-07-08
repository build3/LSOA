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
 *   filtered observations. With merge ability it's a little tricky. There is need
 *   to re-calculate and update merged data when slider's value change in order to provide
 *   correct merge ability. So right now when construct is merged, updates to `verticalStarChart`
 *   is needed otherwise wrong values are showed in table. Obviously there is a need
 *   to update also `horizontalStarChart4` which holds cells for restoring horizontal
 *   level merge.
 * 
 *   To update both of those object two functions are used `swapVerticalStarChart`
 *   and `swapHorizontalStarChart`.
 *
 *   First one iterates through filtered observations by course and calculates
 *   new color and number of observations for cells inside `verticalStarChart` changes their datasets
 *   color, and innerHTML value. New colors are set to `classes` array when
 *   are stored all elements for heat-map. Number of observations are changed
 *   in `quantities` array which stores cells with number of observations.
 *
 *   Second one also iterates through filtered observations and calculates new color
 *   and number of observations for cells inside `horizontalStarChart4`. Cells are changed
 *   in `cells` property of `horizontalStarChart4` which is an array. `cells` contains
 *   all cells (both heat-map and number of observations cells). Color and number of observations
 *   are changed for every cell inside this array.
 *
 * 4. Use filtered observations and new quantity of observations to calculate new color for cell.
 * 
 * 5. Change color in cells and value below them.
 * 
 */

(() => {
    const observations = JSON.parse(window.observations) || {};
    const COLORS_DARK = JSON.parse(window.COLORS_DARK);
    const allStarsCount = parseInt(window.allObservations);

    var start = new Date();
    var elements = $('.chart-4').find('.heatmap-elem');
    window.chartChanged = false;

    // Describes how much time have to pass between `recalculateAll` call (in milliseconds).
    const time = 100;
    var newValue = 0;
    var oldValue = 0;

    $('#date-slider').slider({
        orientation: 'horizontal',
        min: dateToTime(window.minDate),
        max: dateToTime(window.maxDate),
        change: change,
        slide: slide
    });

    // Set start value to min date available in slider.
    $('#slider-value').html(`Observations
        to: ${formatDate($('#date-slider').slider("option", "min"))}`);

    /**
     * Changes element which displays current date. Called when moving slider.
     */
    function slide(event, ui) {
        $("#slider-value").html(`Observations to: ${formatDate(ui.value)}`);

        // Start recalculating cells after some time
        if (new Date() - start > time) {
            recalculateAll(ui);

            start = new Date();
        }
    }

    /**
     * Function called when value in slider change.
     * Filters observations by current date on slider.
     */
    function change(event, ui) {
        recalculateAll(ui);
    }

    function recalculateAll(ui) {
        var observationsFiltered = {};
        var courseObservations = {};
        var horizontalCourse = {};

        // Add 60 seconds here to do get same observations as in start.
        var timestamp = new Date(ui.value);
        timestamp = timestamp.setSeconds(timestamp.getSeconds() + 60);

        // Filter observations.
        for (var construct in observations) {
            observationsFiltered[construct] = {};
            courseObservations[construct] = {};
            horizontalCourse[construct] = {};

            for (var course in observations[construct]) {
                // Check if construct was merged or not to change values
                // per course or all values inside table.
                if (window.mergedConstructs.includes(construct)) {
                    if (!observationsFiltered[construct].hasOwnProperty(0)) {
                        observationsFiltered[construct][0] = {};
                    }

                    courseObservations[construct][course] = {};
                    horizontalCourse[construct][course] = {};

                    for (var sublevel in observations[construct][course]) {
                        const filtered = observations[construct][course][sublevel]
                            .filter(date => date <= timestamp);

                        if (observationsFiltered[construct][0][sublevel] === undefined) {
                            observationsFiltered[construct][0][sublevel] = [];
                            observationsFiltered[construct][0][sublevel] = filtered;
                        } else {
                            observationsFiltered[construct][0][sublevel] =
                                observationsFiltered[construct][0][sublevel]
                                    .concat(filtered);
                        }

                        courseObservations[construct][course][sublevel] = filtered;
                        horizontalCourse[construct][course][sublevel] = filtered;
                        newValue += filtered.length;
                    }
                } else {
                    observationsFiltered[construct][course] = {};
                    horizontalCourse[construct][course] = {};

                    for (var sublevel in observations[construct][course]) {
                        const filtered = observations[construct][course][sublevel]
                            .filter(date => date <= timestamp);

                        observationsFiltered[construct][course][sublevel] = filtered;
                        horizontalCourse[construct][course][sublevel] = filtered;
                        newValue += filtered.length;
                    }
                }
            }
        }

        // Swap verticalStarChart and horizontalStarChart content if any of construct was merged.
        swapVerticalStarChart(courseObservations);
        swapHorizontalStarChart(horizontalCourse);

        // Change elements in table when something changed.
        if (newValue !== oldValue) {
            updateTable(observationsFiltered, joinMergedSublevels(observationsFiltered));

            oldValue = newValue;
        }
    }

    /**
     * Update all tables in chart with new colors and numbers of observations
     * using filtered observations.
     *
     * @param {Object} observationsFiltered - Observations filtered by date.
     * @param {Array} levels - merged Levels horizontally.
     */
    function updateTable(observationsFiltered, levels) {
        if (window.chartChanged) {
            elements = $('.chart-4').find('.heatmap-elem');
        }

        async.each(elements, function(elem, callback) {
            const dataElem = elem.dataset.elem.split('-');
            const construct = dataElem[1];
            const course = dataElem[2];

            var sublevel = dataElem[3];
            var size = 0;

            if (elem.dataset.sublevel === undefined || elem.dataset.sublevel.includes('level')) {
                if (sublevel === 'level') {
                    sublevel = dataElem[4];
                }

                size = levels[construct][sublevel][course].length;
            } else {
                size = observationsFiltered[construct][course][sublevel].length;
            }

            if (size !== elem.dataset.stars) {
                const color = calculateNewColor(size);

                if (elem.classList.contains('heat-elem')) {
                    elem.setAttribute('bgcolor', color);
                    elem.dataset.color = color;
                } else {
                    elem.innerHTML = size;
                    elem.dataset.stars = size;
                }
            }
        })

        window.chartChanged = false;
    }

    /**
     * Calculates new color when value in slider change. To get new color for level
     * new percent value is calculated. When starAmount is 0 color for 0% is used.
     * When starAmount is equal to `allStarsCount` then color with `10` key is returned.
     * If new `percentValue` is less than 10% `LESS_THEN_10` key is used.
     * Otherwise color is taken from the first digit from new `percentValue`. For example when
     * `percentValue` is 73% the first digit is 7 and `7` key is used to get value from `COLORS_DARK` dict.
     * @param {Integer} starAmount 
     */
    function calculateNewColor(starAmount) {
        if (starAmount == 0) {
            return COLORS_DARK["0"];
        }

        if (starAmount == allStarsCount) {
            return COLORS_DARK["10"];
        }

        const percentValue = 100 * starAmount / allStarsCount;

        if (percentValue < 10) {
            return COLORS_DARK["LESS_THEN_10"];
        } else {
            return COLORS_DARK[percentValue.toString()[0]];
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

    /**
     * Change values for cells in verticalStarChart map.
     * @param {Object} observations
     */
    function swapVerticalStarChart(observations) {
        for (var construct in observations) {
            if (window.mergedConstructs.includes(construct)) {
                swapData(observations, construct);
            }
        }
    }

    /**
     * Swap data in cells stored inside `window.verticalStarChart` object for specific construct.
     * @param {Object} observations
     * @param {String} construct
     */
    function swapData(observations, construct) {
        var levels = joinMergedSublevelsDelete(observations);

        Object.keys(observations[construct]).forEach((course, index) => {
            Object.keys(observations[construct][course]).forEach((sublevel, j) => {
                if (!Array.isArray(observations[construct][course][sublevel])) {
                    const level = observations[construct][course][sublevel];
                    const size = levels[construct][level][course].length;
                    const color = calculateNewColor(size);
                    const classes = window.verticalStarChart[construct][index].classes;
                    const quantities = window.verticalStarChart[construct][index].quantities;

                    let heatElem = classes[[...Array(classes.length).keys()]
                        .filter(i => $(classes[i]).hasClass(`heat-level-${level}`))[0]];
                    let quantityElem = quantities[[...Array(quantities.length).keys()]
                        .filter(i => $(quantities[i]).hasClass(`star-level-${level}`))[0]];

                    heatElem.dataset.color = color;
                    heatElem.setAttribute('bgcolor', color);

                    quantityElem.dataset.stars = size;
                    quantityElem.innerHTML = size;
                } else {
                    const size = observations[construct][course][sublevel].length;
                    const color = calculateNewColor(size);

                    let heatElem = window.verticalStarChart[construct][index].classes[j + 1];
                    let quantityElem = window.verticalStarChart[construct][index].quantities[j + 1];

                    if (heatElem !== undefined) {
                        heatElem.dataset.color = color;
                        heatElem.setAttribute('bgcolor', color);

                        quantityElem.dataset.stars = size;
                        quantityElem.innerHTML = size;
                    }
                }
            })
        })
    }

    function swapHorizontalStarChart(observations) {
        for (var construct in observations) {
            swapHorizontalData(construct, observations);
        }
    }

    /**
     * Swap data in cells stored inside `window.horizontalStarChart4` object for specific level.
     * @param {String} construct
     * @param {Object} observations
     */
    function swapHorizontalData(construct, observations) {
        for (level in window.mergedSublevels[construct]) {
            var cells = window.horizontalStarChart4[level].cells

            for (var i = 0; i < cells.length; i++) {
                var sublevel = window.mergedSublevels[construct][level][i];

                for (var j = 0; j < cells[i].length / 2; j++) {
                    let heatElem = cells[i][2 * j];
                    let starElem = cells[i][2 * j + 1];
                    const course = $(heatElem).attr('class').split('-')[2];

                    const size = observations[construct][course][sublevel].length;
                    const color = calculateNewColor(size);

                    heatElem.dataset.color = color;
                    heatElem.setAttribute('bgcolor', color);

                    starElem.dataset.stars = size;
                    starElem.innerHTML = size;
                }
            }
        }
    }

    /**
     * Iterate through all construct in observations and when sublevels were
     * merge into single level and change observations of sublevel to level id as String.
     * In addition calculate number of observations for every merged level by course.
     * This is used to check what sublevels were merged into single level.
     * For example when sublevels 72 and 73 were merged then their keys
     * in object which contains filtered observations instead of having timestamp
     * will have level id.
     *
     * Start => 72: [1111111, 1111111], 73: [1111111, 1111111]
     * End => 72: "18", 73: "18"
     *
     * This function returns object which contains quantity of observations
     * for merged levels.
     *
     * @param {Object} observationsFiltered 
     */
    function joinMergedSublevels(observationsFiltered) {
        var levels = {};

        for (var construct in observationsFiltered) {
            var wasMergedHorizontally = window.mergedSublevels[construct] !== undefined
                && Object.keys(window.mergedSublevels[construct]).length !== 0;

            if (wasMergedHorizontally) {
                levels[construct] = joinSublevels(construct, observationsFiltered);
            }
        }

        return levels;
    }

    /**
     * Iterate through all construct in observations and when sublevels were
     * merge into single level and change observations of sublevel to level id as String.
     * In addition calculate number of observations for every merged level by course.
     * In the end remove those sublevel's keys which id of level is repeated.
     * This let me then iterate throught every cells without repeating those sublevels
     * which were merged.
     *
     * Start => 72: [1111111, 1111111], 73: [1111111, 1111111]
     * End => 72: "18"
     *
     * This is used when swapping data in `verticalStarChart`.
     *
     * This function returns object which contains quantity of observations
     * for merged levels.
     * @param {Object} observationsFiltered 
     */
    function joinMergedSublevelsDelete(observationsFiltered) {
        var levels = {};

        for (var construct in observationsFiltered) {
            var wasMergedHorizontally = window.mergedSublevels[construct] !== undefined
                && Object.keys(window.mergedSublevels[construct]).length !== 0;

            if (wasMergedHorizontally) {
                levels[construct] = joinSublevelsDelete(construct, observationsFiltered);
            }
        }

        return levels;
    }

    /**
     * Calculates number of observations for merged levels and swap value for sublevels in
     * filtered observations.
     * @param {String} construct
     * @param {Object} observationsFiltered
     */
    function joinSublevels(construct, observationsFiltered) {
        var levels = {};

        for (var level in window.mergedSublevels[construct]) {
            levels[level] = {};
            var mLevel = window.mergedSublevels[construct][level];

            for (course in observationsFiltered[construct]) {
                var amount = [];

                for (var i = 0; i < mLevel.length; i++) {
                    amount = amount.concat(observationsFiltered[construct][course][mLevel[i]]);
                    observationsFiltered[construct][course][mLevel[i]] = level;
                }

                levels[level][course] = amount;
            }
        }

        return levels;
    }

    /**
     * Calculates number of observations for merged levels and swap value for sublevels in
     * filtered observations.
     * Delete sublevels keys when level was used more than one time.
     * @param {String} construct
     * @param {Object} observationsFiltered
     */
    function joinSublevelsDelete(construct, observationsFiltered) {
        var levels = {};

        for (var level in window.mergedSublevels[construct]) {
            levels[level] = {};
            var mLevel = window.mergedSublevels[construct][level];

            for (course in observationsFiltered[construct]) {
                var amount = [];

                for (var i = 0; i < mLevel.length; i++) {
                    amount = amount.concat(observationsFiltered[construct][course][mLevel[i]]);

                    if (i === 0) {
                        observationsFiltered[construct][course][mLevel[i]] = level;
                    } else {
                        delete observationsFiltered[construct][course][mLevel[i]];
                    }
                }

                levels[level][course] = amount;
            }
        }

        return levels;
    }
})()
