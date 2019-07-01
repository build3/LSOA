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
 * 4. Use filtered observations and new quantity of observations to calculate new color for cell.
 * 
 * 5. Change color in cells and value below them.
 * 
 */

(() => {
    const observations = JSON.parse(window.observations) || {};
    const COLORS_DARK = JSON.parse(window.COLORS_DARK);

    $('#date-slider').slider({
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
    }

    /**
     * Function called when value in slider change.
     * Filters observations by current date on slider.
     */
    function change(event, ui) {
        var observationsFiltered = {};
        var allStars = {};
        var courseObservations = {};
        var horizontalCourse = {};

        Object.keys(observations).forEach(construct => allStars[construct] = 0);

        // Add 60 seconds here to do get same observations as in start.
        var timestamp = new Date(ui.value);
        timestamp = timestamp.setSeconds(timestamp.getSeconds() + 60);

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
                        allStars[construct] += filtered.length;
                    }
                } else {
                    observationsFiltered[construct][course] = {};
                    horizontalCourse[construct][course] = {};

                    for (var sublevel in observations[construct][course]) {
                        const filtered = observations[construct][course][sublevel]
                            .filter(date => date <= timestamp);

                        observationsFiltered[construct][course][sublevel] = filtered;
                        horizontalCourse[construct][course][sublevel] = filtered;
                        allStars[construct] += observationsFiltered[construct][course][sublevel].length;
                    }
                }
            }
        }

        // Swap verticalStarChart and horizontalStarChart content if any of construct was merged.
        swapVerticalStarChart(courseObservations, allStars);
        swapHorizontalStarChart(horizontalCourse, allStars);

        // Change elements in table.
        changeElements(observationsFiltered, allStars, joinMergedSublevels(observationsFiltered));
    }

    /**
     * Changes colored cells and those with observations count after filtering observations by date.
     * @param {Object} observationsFiltered - Observations filtered by date.
     * @param {Object} allStars - Observations count per construct.
     */
    function changeElements(observationsFiltered, allStars, levels) {
        for (var construct in observationsFiltered) {
            for (var course in observationsFiltered[construct]) {
                for (var sublevel in observationsFiltered[construct][course]) {
                    var size = observationsFiltered[construct][course][sublevel].length;
                    var color = calculateNewColor(size, allStars[construct]);
                    var observations = observationsFiltered[construct][course][sublevel];

                    // If course is 0 then it means construct was merged.
                    if (parseInt(course)) {
                        if (Array.isArray(observations)) {
                            changeElems(
                                size,
                                color,
                                `.stars-${course}-${sublevel}`,
                                `.heat-${course}-${sublevel}`,
                                construct
                            );
                        } else {
                            const level = observations;
                            size = levels[level][course].length;
                            color = calculateNewColor(size, allStars[construct]);

                            changeElems(
                                size,
                                color,
                                `.star-level-${level}-${course}`,
                                `.heat-level-${level}-${course}`,
                                construct
                            );
                        }
                    } else {
                        if (Array.isArray(observations)) {
                            changeElems(
                                size,
                                color,
                                `.stars-merged-${sublevel}`,
                                `.heat-merged-${sublevel}`,
                                construct
                            );
                        } else {
                            const level = observations;
                            size = levels[level][course].length;
                            color = calculateNewColor(size, allStars[construct]);

                            changeElems(
                                size,
                                color,
                                `.stars-merged-level-${level}`,
                                `.heat-merged-level-${level}`,
                                construct
                            );
                        }
                    }
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
     * Change heat and star td element for single cell.
     * @param {Integer} size - Quantity of observations.
     * @param {String} color - New color for sublevel.
     * @param {String} starsClass - Class to find star element.
     * @param {String} heatClass - Class to find heat element.
     * @param {Integer} construct - ID of current construct.
     */
    function changeElems(size, color, starsClass, heatClass, construct) {
        let elem = $(`.star-chart-4-table-${construct}`)
            .find(heatClass)
            .attr('bgcolor', color);
        elem[0].dataset.color = color;

        elem = $(`.star-chart-4-table-${construct}`)
            .find(starsClass)
            .html(size);
        elem[0].dataset.stars = size;
    }

    /**
     * Change values for cells in verticalStarChart map.
     * @param {Object} observations 
     * @param {Object} allStars - All observations per construct.
     */
    function swapVerticalStarChart(observations, allStars) {
        for (var construct in observations) {
            if (window.mergedConstructs.includes(construct)) {
                swapData(observations, construct, allStars);
            }
        }
    }

    /**
     * Swap data in cells stored inside `window.verticalStarChart` object for specific construct.
     * @param {Object} observations 
     * @param {String} construct 
     * @param {Object} allStars
     */
    function swapData(observations, construct, allStars) {
        var levels = joinMergedSublevelsDelete(observations);

        Object.keys(observations[construct]).forEach((course, index) => {
            Object.keys(observations[construct][course]).forEach((sublevel, j) => {
                if (!Array.isArray(observations[construct][course][sublevel])) {
                    const level = observations[construct][course][sublevel];
                    const size = levels[level][course].length;
                    const color = calculateNewColor(size, allStars[construct]);
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
                    const color = calculateNewColor(size, allStars[construct]);

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

    /**
     * Add to sublevel key, value which is a sublevel's level when level was merged.
     * @param {Object} observationsFiltered 
     */
    function joinMergedSublevels(observationsFiltered) {
        var levels = {};

        for (var construct in observationsFiltered) {
            var wasMergedHorizontally = window.mergedSublevels[construct] !== undefined
                && Object.keys(window.mergedSublevels[construct]).length !== 0;

            if (wasMergedHorizontally) {
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
            }
        }

        return levels;
    }

    /**
     * Add to sublevel key, value which is a sublevel's level when level was merged.
     * Delete sublevel keys when level was used more than one time.
     * @param {Object} observationsFiltered 
     */
    function joinMergedSublevelsDelete(observationsFiltered) {
        var levels = {};

        for (var construct in observationsFiltered) {
            var wasMergedHorizontally = window.mergedSublevels[construct] !== undefined
                && Object.keys(window.mergedSublevels[construct]).length !== 0;

            if (wasMergedHorizontally) {
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
                                delete observationsFiltered[construct][course][mLevel[i]]
                            }
                        }

                        levels[level][course] = amount;
                    }
                }
            }
        }

        return levels;
    }

    function swapHorizontalStarChart(observations, allStars) {
        for (var construct in observations) {
            swapHorizontalData(construct, allStars, observations);
        }
    }

    /**
     * Swap data in cells stored inside `window.horizontalStarChart4` object for specific level.
     * @param {String} construct 
     * @param {Object} allStars 
     * @param {Object} observations
     */
    function swapHorizontalData(construct, allStars, observations) {
        for (level in window.mergedSublevels[construct]) {
            var cells = window.horizontalStarChart4[level].cells

            for (var i = 0; i < cells.length; i++) {
                var sublevel = window.mergedSublevels[construct][level][i];

                for (var j = 0; j < cells[i].length / 2; j++) {
                    let heatElem = cells[i][j + j];
                    let starElem = cells[i][j + j + 1];
                    const course = $(heatElem).attr('class').split('-')[2];

                    const size = observations[construct][course][sublevel].length;
                    const color = calculateNewColor(size, allStars[construct]);

                    heatElem.dataset.color = color;
                    heatElem.setAttribute('bgcolor', color);

                    starElem.dataset.stars = size;
                    starElem.innerHTML = size;
                }
            }
        }
    }
})()
