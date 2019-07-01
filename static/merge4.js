/**
 * This file contains merge ability for star chart v4.
 */

(() => {
    const COLORS_DARK = JSON.parse(window.COLORS_DARK);
    const CLASS_COLUMN = 1;

    var startIndex = 0;

    window.horizontalStarChart4 = {};
    window.verticalStarChart = {};
    window.mergedConstructs = [];
    window.mergedSublevels = {};

    $('.separateVertical-4').hide();

    /**
     * Remake tooltips to create new tooltip after separating merged level.
     */
    function remakeTooltips() {
        // Remake tooltips.
        var is_touch_device = (
            ("ontouchstart" in window)
            || window.DocumentTouch
            && document instanceof DocumentTouch
        );

        if (is_touch_device) {
            $('[data-toggle="tooltip"]').tooltip({trigger: 'click'});
        } else {
            $('[data-toggle="tooltip"]').tooltip({trigger: 'hover'});
        }
    }

    function addHeaderAfter(header, startIndex, levelId, levelName) {
        $(header)
            .find('th')
            .eq(startIndex + 1)
            .after(`<th style="text-align:center;" class="align-middle sublevel" ` +
                `scope="col" data-toggle="tooltip" data-level-id="${levelId}">${levelName}</th>`);
    }

    function addHeaderBefore(header, startIndex, levelId, levelName) {
        $(header)
            .find('th')
            .eq(startIndex + 1)
            .before(`<th style="text-align:center;" class="align-middle sublevel" ` +
                `scope="col" data-toggle="tooltip" data-level-id="${levelId}">${levelName}</th>`);
    }

    /**
     * Removes and returns columns which are merged in addition sets startIndex.
     * @param {Array} headers 
     * @param {Integer} i 
     * @param {Integer} constructId 
     * @param {String} construct 
     */
    function findCells(headers, i, constructId, construct) {
        const cellIndex = headers[i].cellIndex;

        if (i == 0) {
            startIndex = cellIndex;
        }

        return $(`.star-chart-4-table-${constructId} .${construct}`)
            .find(`td:eq(${cellIndex})`);
    }

    /**
     * Gets cells for merged level.
     * @param {Array} headers 
     * @param {Integer} levelId 
     * @param {Integer} constructId 
     * @param {String} construct 
     */
    function getCells4(headers, constructId, construct) {
        var stars = [];
    
        [...Array(headers.length).keys()].map(i => {
            stars[i] = findCells(headers, i, constructId, construct);
        });
    
        return stars;
    }

    /**
     * Gets all headers for specific level ID and construct ID.
     * @param {Integer} constructId 
     * @param {Integer} levelId 
     */
    function getAllHeaders4(constructId, levelId) {
        return $(`.star-chart-4-table-${constructId} tr:eq(1)`)
            .find(`[data-level-id='${levelId}']`);
    }

    /**
     * Checks if level is last in table.
     * @param {Integer} constructId 
     * @param {String} construct 
     * @param {Array} headers 
     * @param {Integer} levelCount 
     */
    function isLastLevel4(constructId, construct, headers, levelCount) {
        const cellIndex = headers[0].cellIndex;

        const cells = $(`.star-chart-4-table-${constructId} .${construct}`)
            .find(`td:eq(0)`);
        startIndex = cellIndex;
        const allHeaders = $(`.star-chart-4-table-${constructId}`)
            .find('th');

        return startIndex + (headers.length) + CLASS_COLUMN === allHeaders.length - levelCount
    }

    function getAllStars(constructId) {
        const cells = $(`.star-chart-4-table-${constructId}`).find('.stars-amount');
        return [...Array(cells.length).keys()].reduce(
                (acc, val) => acc += $(cells[val]).data('stars'), 0);
    }

    function createNewCells(amount, allStars, i, constructId, levelId, courseId) {
        const newColor = calculateNewColor(amount, allStars);
        const heatRow = 2;
        const starRow = 3;

        var heatMapElement = $(document.createElement('td'))
            .addClass(`text-center heat-level-${levelId} heat-level-${levelId}-${courseId}`)
            .attr('bgcolor', newColor);

        heatMapElement[0].dataset.cslId = "";
        heatMapElement[0].dataset.color = newColor;

        var starElement = $(document.createElement('td'))
            .addClass(`text-center stars-amount star-level-${levelId} star-level-${levelId}-${courseId}`)
            .append(`<span>${amount}</span>`);

        starElement[0].dataset.cslId = "";
        starElement[0].dataset.stars = amount;

        if (isLast) {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${i + heatRow + i})`)
                .find('td')
                .eq(startIndex - 1)
                .after(heatMapElement[0]);

            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${i + starRow + i})`)
                .find('td')
                .eq(startIndex - 1)
                .after(starElement[0]);
        } else {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${i + heatRow + i})`)
                .find('td')
                .eq(startIndex)
                .before(heatMapElement[0]);

            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${i + starRow + i})`)
                .find('td')
                .eq(startIndex)
                .before(starElement[0]);
            }
    }

    function insertOldHeader(isLast, constructId, header) {
        if (isLast) {
            $($(`.star-chart-4-table-${constructId} tr:eq(1)`).first())
                .find('th')
                .eq(startIndex - 1)
                .after(header);
        } else {
            $($(`.star-chart-4-table-${constructId} tr:eq(1)`).first())
                .find('th')
                .eq(startIndex)
                .before(header);
        }
    }

    function insertOldCell(isLast, constructId, cell, row) {
        if (isLast) {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${row})`)
                .find('td')
                .eq(startIndex - 1)
                .after(cell);
        } else {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${row})`)
                .find('td')
                .eq(startIndex)
                .before(cell);
        }
    }

    function recalculateObservations(amount, headers, constructId, cells) {
        const total = amount.reduce((acc, val) => acc += val, 0);
        var newCells = [];

        for (var i = headers.length - 1; i >= 0; i--) {
            const size = amount[i];
            const color = calculateNewColor(size, getAllStars(constructId) + total);
            const sublevelId = $(cells[i][0]).data('sublevel');

            newCells[i] = [];

            var heatMapElement = $(document.createElement('td'))
                .addClass(`text-center heat-${sublevelId}`)
                .attr('bgcolor', color);

            heatMapElement[0].dataset.cslId = "";
            heatMapElement[0].dataset.color = color;
            heatMapElement[0].dataset.sublevel = sublevelId

            var starElement = $(document.createElement('td'))
                .addClass(`text-center stars-${sublevelId} stars-amount`)
                .append(`<span>${size}</span>`);

            starElement[0].dataset.cslId = "";
            starElement[0].dataset.stars = size;

            newCells[i].push(heatMapElement);
            newCells[i].push(starElement);
        }

        return newCells;
    }

    $('.horizontal-unmerge-4').hide();

    $('.horizontal-merge-4').click(function() {
        const levelId = $(this).attr('id').split('-')[2]
        const sublevelsAmount = $(this).data('sublevels');
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const levelName = $(this).data('level-name');
        const levelCount = $(this).data('levels-count');

        // No reason to merge when only one sublevel is used.
        if (sublevelsAmount > 1) {
            if (window.mergedConstructs.includes(constructId)) {
                // Just use one case and trigger it all the time
                // to fully control behaviour of merging with this single case.
                // It's complicated enough, so let's use one case only instead writing all of them.
                // This is only needed when two buttons are used simultaneously.
                $(`#separateVertical-4-${constructId}`).trigger("click");
                $(this).trigger("click");
                $(`#mergeVertical-4-${constructId}`).trigger("click");
            } else {
                // Get all headers for level.
                var headers = getAllHeaders4(constructId, levelId);

                // Hide tooltips for merged headers.
                [...Array(headers.length).keys()].forEach(i => $(headers[i]).tooltip("hide"));

                window.horizontalStarChart4[levelId] = {
                    'headers': headers,
                    'cells': getCells4(headers, constructId, construct)
                };

                // Check if merged sublevels are inside last level in table.
                isLast = isLastLevel4(constructId, construct, headers, levelCount);
                headers.remove();

                // Get first <th> element for specific table.
                var header = $(`.star-chart-4-table-${constructId} tr:eq(1)`).first();

                // If merged level is last inside table I have to add new header after the last element which left.
                // Otherwise add new header before sublevel which was first inside table before removing it.
                if (isLast) {
                    addHeaderAfter(header, startIndex - 2, levelId, levelName);
                } else {
                    addHeaderBefore(header, startIndex - 1, levelId, levelName);
                }

                const cells = window.horizontalStarChart4[levelId].cells;
                const allStars = getAllStars(constructId);
                const classQuantity = cells[0].length / 2;

                var amount = [...Array(classQuantity).keys()].map(() => 0);

                // Calculate amount of stars per course, and remove unneded cells.
                for (var i = 0; i < cells.length; i++) {
                    for (var j = 0; j < classQuantity; j++) {
                        amount[j] += parseInt(cells[i][j + j + 1].dataset.stars);
                    }

                    $(cells[i]).remove();
                }

                const classesIds = [];

                // Createa array with courses id's.
                for (var i = 0; i < cells[0].length / 2; i++) {
                    classesIds.push($(cells[i][i + i]).attr('class').split('-')[2]);
                }

                // Create new cells with colors and calculated earlier amount.
                for (var i = 0; i < classQuantity; i++) {
                    createNewCells(amount[i], allStars, i, constructId, levelId, classesIds[i]);
                }

                // Change colspan of parent th element to 1.
                $(this).parent().attr('colspan', 1);
                $(this).hide();
                $(`#horizontal-back-4-${levelId}`).show();

                var sublevelIds = [...Array(cells.length).keys()].reduce(
                    (acc, i) => acc.concat($(cells[i][0]).data('sublevel')), []);

                if (window.mergedSublevels.hasOwnProperty(constructId)) {
                    window.mergedSublevels[constructId][levelId] = sublevelIds;
                } else {
                    window.mergedSublevels[constructId] = {};
                    window.mergedSublevels[constructId][levelId] = sublevelIds;
                }
            }
        }
    })

    $('.horizontal-unmerge-4').click(function() {
        const levelId = $(this).attr('id').split('-')[3]
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const levelCount = $(this).data('levels-count');

        var header = $(`.star-chart-4-table-${constructId} tr:eq(1)`)
            .find(`[data-level-id="${levelId}"]`);
        var isLast = isLastLevel4(constructId, construct, header, levelCount);

        findCells(header, 0, constructId, construct).remove();
        header.remove();

        // Get observations which were merged for current levelId.
        const cells = window.horizontalStarChart4[levelId].cells;
        const headers = window.horizontalStarChart4[levelId].headers;

        // If unmerging when vertical merge is on, recalculate observations for all classes.
        if (window.mergedConstructs.includes(constructId)) {
            var amount = [];

            // Calculate amount of observations for sublevels in single level.
            for (var i = 0; i < headers.length; i++) {
                amount.push(0);

                for (var j = 0; j < cells[0].length / 2; j++) {
                    amount[i] += $(cells[i][j + j + 1]).data('stars');
                }
            }

            const newCells = recalculateObservations(amount, headers, constructId, cells);

            for (var i = headers.length - 1; i >= 0; i--) {
                insertOldHeader(isLast, constructId, headers[i]);
    
                for (var j = 0; j < newCells[i].length; j++) {
                    insertOldCell(isLast, constructId, newCells[i][j], j + 2);
                }
            }
        } else {
            for (var i = headers.length - 1; i >= 0; i--) {
                insertOldHeader(isLast, constructId, headers[i]);
    
                for (var j = 0; j < cells[i].length; j++) {
                    insertOldCell(isLast, constructId, cells[i][j], j + 2);
                }
            }
        }

        let parent = $(this).parent();
        parent.attr('colspan', parent.data('sublevels'));

        $(this).hide();
        $(`#horizontal-4-${levelId}`).show();

        remakeTooltips();

        var array = window.verticalStarChart[constructId];
        var newArray = [];
        var newArray2 = [];

        if (window.mergedConstructs.includes(constructId)) {
            // Update state of verticalArray to restore good elements.
            for (var i in array) {
                // Get level element.
                const elem = array[i].classes.filter(elem => $(elem).hasClass(`heat-level-${levelId}`));
                var index = array[i].classes.indexOf(elem[0]);
                
                // Splice arrays by index of level element.
                array[i].classes.splice(index, 1);
                array[i].quantities.splice(index, 1);

                // Create new array with spliced elements
                newArray[i] = array[i].classes.splice(0, index);
                newArray2[i] = array[i].quantities.splice(0, index);
            }

            // Push cells into new array.
            for (var j = 0; j < cells[0].length / 2; j++) {
                for (var i in cells) {
                    newArray[j].push(cells[i][j + j]);
                    newArray2[j].push(cells[i][j + j + 1]);
                }
            }

            // Concat old cells with new cells.
            for (var i in array) {
                array[i].classes = newArray[i].concat(array[i].classes);
                array[i].quantities = newArray2[i].concat(array[i].quantities);
            }
        }

        delete window.mergedSublevels[constructId][levelId];
    })

    /* ------------------------------------------------------------------------ */

    $('.mergeVertical-4').click(function() {
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];

        // Need to calculate it dynamically.
        const sublevels = $(`.star-chart-4-table-${constructId}`).find('.sublevel').length;
        const mergedLevels = window.mergedSublevels[construct];

        // Create object which let restore removed cells later.
        createObjectToRestore(constructId, sublevels);

        // Initialize array with 0 for every sublevel.
        var observationQuantity = initQuantityArray(sublevels);
        var sublevelsIds = [];

        // Calculate amount of observations per sublevel and append their ids to `sublevelIds` array.
        for (var i in window.verticalStarChart[constructId]) {
            for (var j in window.verticalStarChart[constructId][i].quantities) {
                if (j != "0") {
                    const stars = window.verticalStarChart[constructId][i].quantities[j].dataset.stars;
                    observationQuantity[j - 1] += parseInt(stars);

                    const sublevel = $(window.verticalStarChart[constructId][i].classes[j]).data('sublevel')

                    if (sublevel === undefined) {
                        var level = $(window.verticalStarChart[constructId][i].classes[j])
                            .attr('class').split('-')[3];
                        level = level.split(' ')[0];

                        sublevelsIds.push(`level-${level}`);
                    } else {
                        sublevelsIds.push(sublevel);
                    }
                }
            }
        }

        // Remove cells stored in `verticalStarChart` object.
        removeCells(constructId);

        // Append rows with new values to table.
        var tbody = $(this).parent().parent().parent().next();
        appendNewRows(observationQuantity, sublevelsIds, tbody, constructId);

        // Save construct id to lookup if it was merged or not.
        window.mergedConstructs.push(constructId);
        $(this).hide();
        $(`#separateVertical-4-${constructId}`).show();
    })

    /**
     * Creates array which allow to restore removed cells.
     * @param {Integer} constructId 
     * @param {Integer} sublevels - Number of sublevels in construct.
     * @param {Integer} classesColumn - Number of columns with courses.
     */
    function createObjectToRestore(constructId, sublevels) {
        var classes = $(`.star-chart-4-table-${constructId} .heat-row`).find('td');
        var quantities = $(`.star-chart-4-table-${constructId} .quantity-row`).find('td');

        classes = partition(classes, sublevels + CLASS_COLUMN);
        quantities = partition(quantities, sublevels + CLASS_COLUMN);

        [...Array(classes.length).keys()].forEach((index) => {
            if (!window.verticalStarChart.hasOwnProperty(constructId)) {
                window.verticalStarChart[constructId] = {}
            }
            
            window.verticalStarChart[constructId][index] = {
                'classes': classes[index],
                'quantities': quantities[index]
            }
        });
    }

    function initQuantityArray(sublevels) {
        return [...Array(sublevels).keys()].reduce((acc, number) => {
            acc.push(0)
            return acc;
        }, []);
    }

    /**
     * Remove saved cells.
     * @param {Integer} constructId 
     */
    function removeCells(constructId) {
        for (var i in window.verticalStarChart[constructId]) {
            for (var j in window.verticalStarChart[constructId][i].quantities) {
                $(window.verticalStarChart[constructId][i].quantities[j]).remove();
                $(window.verticalStarChart[constructId][i].classes[j]).remove();
            }
        }
    }

    /**
     * Appends new rows with td's to tbody.
     * @param {Array} observationQuantity 
     * @param {Array} sublevelsIds 
     * @param {Selector} tbody 
     * @param {Integer} constructId 
     */
    function appendNewRows(observationQuantity, sublevelsIds, tbody, constructId) {
        $(tbody).find('tr').remove();
        $(tbody).append(`<tr class="construct-${constructId} merged-row"></tr>`);
        $(tbody).append(`<tr class="construct-${constructId} merged-row"></tr>`);

        var tr = $(tbody).find('tr');
        $(tr[0]).append('<td><b>All courses</b></td>');
        $(tr[1]).append('<td></td>');

        const allStars = [...Array(observationQuantity.length).keys()].reduce((acc, i) =>
            acc += observationQuantity[i], 0);

        for (var i = 0; i < observationQuantity.length; i++) {
            const stars = observationQuantity[i];
            const color = calculateNewColor(stars, allStars);
            var id = sublevelsIds[i];

            $(tr[0]).append(`<td data-csl-id="" class="text-center heat-merged-${id}"
                data-color="${color}" bgcolor="${color}"></td>`);
            $(tr[1]).append(`<td data-csl-id="" data-stars="${stars}"
                class="text-center stars-merged-${id} stars-amount"><span>${stars}</span></td>`);
        }
    }

    $('.separateVertical-4').click(function() {
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];

        // Remove all cells from tbody.
        var tbody = $(this).parent().parent().parent().next();
        $(tbody).find('tr').remove();

        // Create new rows, append them to tbody and then append td's to rows.
        for (var i in window.verticalStarChart[constructId]) {
            var heatRow = $(document.createElement('tr'))
                .addClass(`construct-${constructId} heat-row`);

            var quantityRow = $(document.createElement('tr'))
                .addClass(`construct-${constructId} thicker quantity-row`); 

            $(tbody).append(heatRow);
            $(tbody).append(quantityRow);

            for (var j in window.verticalStarChart[constructId][i].classes) {
                $(heatRow[0]).append(window.verticalStarChart[constructId][i].classes[j])
            }

            for (var j in window.verticalStarChart[constructId][i].quantities) {
                $(quantityRow[0]).append(window.verticalStarChart[constructId][i].quantities[j])
            }
        }

        // Remove construct from mergedConstructs.
        var index = window.mergedConstructs.indexOf(constructId);

        if (index > -1) {
            window.mergedConstructs.splice(index, 1);
        }

        $(this).hide();
        $(`#mergeVertical-4-${constructId}`).show();
    })

    function partition(array, n) {
        return array.length ? [array.splice(0, n)].concat(partition(array, n)) : [];
    }

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
})()
