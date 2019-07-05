(() => {
    // Columns which are not used to display stars (students, buttons).
    const NOT_STAR_COLUMNS = 2;

    // Horizontal sublevels which were merged.
    var mergedHorizontalLevels = {};

    // Describes in what position new elements are added to table.
    var startIndex = 0;

    // Number of rows which end class or multiple classes.
    var endClasses = [];

    // Vertical merged students by class.
    var mergedVertical = {};

    // Stores id of merged courses per construct.
    var mergingStatus = {};

    // Stores id of levels which were merged per construct.
    var mergedLevels = {};

    /**
     * Initialize `mergingStatus` and `mergedLevels` with every construct id in chart.
     */
    function initializeMergingStatus() {
        const tables = $('body').find('.chart');

        [...Array(tables.length).keys()].forEach(i => {
            mergingStatus[$(tables[i]).data('construct')] = [];
            mergedLevels[$(tables[i]).data('construct')] = [];
        });
    }

    initializeMergingStatus();

    /**
     * Adds new column to table.
     * @param {Array} starAmount - Amount of observation per student.
     * @param {Integer} startIndex - Position inside table where new elements are created.
     * @param {Integer} constructId - ID of construct
     * @param {Integer} i - Index element.
     * @param {Boolean} isLast - Describes if level was last in table.
     */
    function addColumn(starAmount, startIndex, constructId, i, isLast, levelId) {
        if (starAmount.length !== 0) {
            addColumnWithStar(startIndex, constructId, starAmount, i, isLast, levelId);
        } else if (isLast) {
            addEmptyCellAfter(constructId, i + 1, startIndex - NOT_STAR_COLUMNS - 1, levelId);
        } else {
            addEmptyCellBefore(constructId, i + 1, startIndex - NOT_STAR_COLUMNS, levelId);
        }
    }

    function addColumnWithStar(startIndex, constructId, stars, rowIndex, isLast, levelId) {
        let span = createSpan(stars);

        if (isLast) {
            starColumnAfter(rowIndex + 1, constructId,
                startIndex - NOT_STAR_COLUMNS - 1, stars, span, levelId);
        } else {
            starColumnBefore(rowIndex + 1, constructId,
                startIndex - NOT_STAR_COLUMNS, stars, span, levelId);
        }
    }

    function addTooltip() {
        return '<i data-toggle="tooltip" title="" class="fa fa-star"></i>';
    }

    /**
     * Check if level is last inside table.
     * Level is last when sum of his `startIndex` and `<th>` elements is
     * equal to all headers inside table - cells for students name(Those are maked with <th> too)
     * and - count of levels for construct.
     * @param {Integer} constructId 
     * @param {String} construct 
     * @param {Array} headers
     * @param {Integer} levelCount 
     */
    function isLastLevel(constructId, construct, headers, levelCount) {
        const cellIndex = headers[0].cellIndex;

        const cells = $(`.star_chart_table-${constructId} .${construct}`)
            .find(`td:eq(0)`);
        startIndex = cellIndex;
        const allHeaders = $(`.star_chart_table-${constructId}`)
            .find('th');
    
        // The calculations here checks if sublevel or level which is merging is last in corresponding table.
        // To check if sublevel or level is last I sum `startIndex` (first column number of <th> elements for single level)
        // and quantity of all headers for single level `(headers.length)` then I check if this is equal
        // to subtraction of quantity of <th> elements in sublevels row, amount of vertical <th> cells(i.e student cells),
        // cells with buttons and then 2 cells wchich are in the same level as buttons.
        return startIndex + (headers.length) === allHeaders.length - (2 * cells.length) - levelCount - 2
    }

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

    /**
     * Creates `<span>` element with number of observations or add space
     * when there are less than one observation inside `stars` array.
     * @param {Array} stars - Contains observations for single sublevel.
     */
    function createSpan(stars) {
        return stars.length > 1 ?
            `<span class="star-number">(${stars.length})</span>` :
            "&nbsp;"
    }

    /**
     * Removes unneded columns before merge.
     * @param {Array} headers - List with <th> elements.
     * @param {Integer} i - Index to lookup headers list.
     * @param {Integer} constructId - ID of clicked construct.
     * @param {String} construct - Name of clicked construct.
     */
    function findCells(headers, i, constructId, construct) {
        const cellIndex = headers[i].cellIndex;

        if (i == 0) {
            startIndex = cellIndex - 1;
        }
        
        // Subtract by 2 cause there are two unneded elements which are counted as well
        // (row with students and row with vertical merge buttons).
        return $(`.star_chart_table-${constructId} .${construct}`)
            .find(`td:eq(${cellIndex - 2})`);
    }

    function addEmptyCellBefore(constructId, j, startIndex, levelId) {
        var element = $(document.createElement('td'))
            .addClass(`text-center level-${levelId}`);
        element[0].dataset.cslId = "";

        if (endClasses.includes(j - 1)) {
            $(element[0]).addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${j + 1})`)
            .find(`td`)
            .eq(startIndex)
            .before(element[0]);
    }

    function addEmptyCellAfter(constructId, j, startIndex, levelId) {
        var element = $(document.createElement('td'))
            .addClass(`text-center level-${levelId}`);
        element[0].dataset.cslId = "";

        if (endClasses.includes(j - 1)) {
            $(element[0]).addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${j + 1})`)
            .find(`td`)
            .eq(startIndex)
            .after(element[0]);
    }

    function starColumnBefore(rowIndex, constructId, startIndex, stars, span, levelId) {
        var element = $(document.createElement('td'))
            .addClass(`text-center level-${levelId}`)
            .append(addTooltip())
            .append(span);

        element[0].dataset.cslId = "";
        element[0].dataset.modalLaunchObservations = `[${stars}]`;

        if (endClasses.includes(rowIndex - 1)) {
            $(element[0]).addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${rowIndex + 1})`)
            .find('td')
            .eq(startIndex)
            .before(element[0]);
    }

    function starColumnAfter(rowIndex, constructId, startIndex, stars, span, levelId) {
        var element = $(document.createElement('td'))
            .addClass(`text-center level-${levelId}`)
            .append(addTooltip())
            .append(span);

        element[0].dataset.cslId = "";
        element[0].dataset.modalLaunchObservations = `[${stars}]`;

        if (endClasses.includes(rowIndex - 1)) {
            $(element[0]).addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${rowIndex + 1})`)
            .find('td')
            .eq(startIndex)
            .after(element[0]);
    }

    function addHeaderAfter(header, startIndex, levelId, levelName) {
        $(header)
            .find('th')
            .eq(startIndex + 1)
            .after(`<th style="text-align:center;" class="align-middle" ` +
                `scope="col" data-toggle="tooltip" data-level-id="${levelId}">${levelName}</th>`);
    }

    function addHeaderBefore(header, startIndex, levelId, levelName) {
        $(header)
            .find('th')
            .eq(startIndex + 1)
            .before(`<th style="text-align:center;" class="align-middle" ` +
                `scope="col" data-toggle="tooltip" data-level-id="${levelId}">${levelName}</th>`);
    }

    /**
     * Returns all <th> for specify construct and level.
     * @param {Integer} constructId 
     * @param {Integer} levelId 
     */
    function getAllHeaders(constructId, levelId) {
        return $(`.star_chart_table-${constructId} tr:eq(1)`)
            .find(`[data-level-id='${levelId}']`);
    }

    /**
     * Returns array with observations id used when merging.
     * @param {Array} stars - Array with <td> elements.
     */
    function calculateStarAmount(stars) {
        var starAmount = {}

        for (var i = 0; i < stars[0].length; i++) {
            starAmount[i] = []

            for (var j = 0; j < stars.length; j++) {
                const observations = $(stars[j][i]).data('modal-launch-observations');
                
                if (observations) {
                    // Add observations and filter reoccurring ones.
                    observations.map(observation => {
                        if (!starAmount[i].some(star => observation === star)) {
                            starAmount[i].push(observation);
                        }
                    });
                }
            }

            $(stars[i]).remove();
        }

        return starAmount;
    }

    /**
     * Add cells which are inside sublevels columns to `stars` array then remove
     * those columns and calculate `startIndex`.
     * In addition each sublevel and his observations
     * are added to mergedHorizontalLevels dictionary.
     */
    function getCells(headers, constructId, construct) {
        var stars = [];

        [...Array(headers.length).keys()].map(i => {
            stars[i] = findCells(headers, i, constructId, construct);
        });

        return stars;
    }

    function getTdsWhichEndClass(stars) {
        return [...Array(stars[0].length).keys()].filter(i => $(stars[0][i]).hasClass('thicker'));
    }

    function restoreSublevelHeader(isLast, constructId, header) {
        var elem = $($(`.star_chart_table-${constructId} tr:eq(1)`).first().find('th'));

        if (isLast) {
            $(elem).eq(startIndex).after(header);
        } else {
            $(elem).eq(startIndex + 1).before(header);
        }
    }

    function restoreSublevelCell(isLast, constructId, cell, row) {
        var elem = $(`.star_chart_table-${constructId}`).find(`tr:eq(${row})`).find('td');

        if (isLast) {
            $(elem).eq(startIndex - 2).after(cell);
        } else {
            $(elem).eq(startIndex - 1).before(cell);
        }
    }

    /**
     * Create new horizontal object to restore when any course in construct is
     * merged and unmerge for any level is clicked. This is needed cause
     * `mergedHorizontalLevels` keeps cells for all students in class instead
     * of all cells for single class.
     *
     * @param {Array} mergedClasses - merged courses.
     * @param {String} levelId - ID of level as string.
     */
    function createNewCellsToRestore(mergedCourses, levelId) {
        var newObservations = {};
        var newCells = {}

        mergedCourses.forEach(id => newObservations[id] = {});

        var cells = mergedHorizontalLevels[levelId].cells;

        for (var i = 0; i < cells.length; i++) {
            newCells[i] = [];

            for (var j = 0; j < cells[i].length; j++) {
                createNewCell(cells, i, j, newObservations, newCells);
            }
        }

        return newCells;
    }

    function createNewCell(cells, i, j, observations, newCells) {
        const courseId = $(cells[i][j]).data('class');
        const stars = ($(cells[i][j]).data('modal-launch-observations') || []);
        const isThicker = $(cells[i][j]).hasClass('thicker');

        if (observations.hasOwnProperty(courseId)) {
            if (observations[courseId].hasOwnProperty(i)) {
                observations[courseId][i] = observations[courseId][i].concat(stars);

                if (isThicker) {
                    addThickerElement(cells, newCells, i, j, observations[courseId][i]);
                }
            } else {
                observations[courseId][i] = [];
                observations[courseId][i] = observations[courseId][i].concat(stars);

                if (isThicker) {
                    addThickerElement(cells, newCells, i, j, observations[courseId][i]);
                }
            }
        } else {
            newCells[i].push(cells[i][j]);
        }
    }

    function addThickerElement(cells, newCells, i, j, newObservations) {
        let observations = Array.from(new Set(newObservations));

        // If observations are empty use saved element. Otherwise
        // create new one.
        if (observations.length === 0) {
            newCells[i].push(cells[i][j]);
        } else {
            let element = $(document.createElement('td'))
                .addClass('text-center thicker')
                .append(addTooltip())
                .append(createSpan(observations));

            element[0].dataset.cslId = "";
            element[0].dataset.modalLaunchObservations = `[${observations}]`;

            newCells[i].push(element[0]);
        }
    }

    /**
     * Recalculate observations for students which are in course
     * which was merged vertically. This is used when both class and level
     * merge were used and unmerging horizontal one of levels.
     *
     * New observations are created in this way:
     *
     * <CourseID>: {
     *   <Sublevel (`i`)>: [[Student1], [Student2]...]   <- Array containing observations for students per sublevel.
     * }
     *
     * @param {Array} mergedCourses - Array with merged courses.
     * @param {Object} cells - observations to recalculate.
     */
    function recalculateHorizontal(mergedCourses, cells) {
        var observations = {};

        mergedCourses.forEach((course) => {
            observations[course] = {};

            for (var i = 0; i < cells.length; i++) {
                observations[course][i] = [];

                for (var j = 0; j < cells[i].length; j++) {
                    const courseId = $(cells[i][j]).data('class');
                    const stars = ($(cells[i][j]).data('modal-launch-observations') || []);

                    if (mergedCourses.indexOf(`${courseId}`) > -1) {
                        observations[course][i].push(stars);
                    }
                }
            }
        })

        return observations;
    }

    /**
     * Update `mergedVertical` object for specific course and construct when
     * unmerging horizontally any level when any course is merged. 
     *
     * @param {Array} mergedCourses - Array with merged courses.
     * @param {String} levelId - level ID as string.
     * @param {String} constructId - construct ID as string.
     * @param {Object} observations - Recalculated observations.
     */
    function updateVerticalRestore(mergedCourses, levelId, constructId, observations) {
        mergedCourses.forEach((course) => {
            var obs = observations[course];
            var restore = mergedVertical[constructId][course];

            Object.keys(obs).forEach(i => {
                for (j = 0; j < obs[i].length; j++) {
                    addSublevelsToVerticalRestore(restore, levelId, obs, course, i, j);
                }
            })
        })
    }

    /**
     * Add sublevels elements which contains recalculated observations to `mergedVertical`
     * object for specific student in specific construct and course.
     *
     * To add those sublevels in good place inside an array. I used element
     * which has `level-{levelID}` class, find his index inside the array,
     * splice the array from 0 to index element + current sublevel index (`i`) +
     * 1 (to grab also level element or created earlier sublevel element).
     * Then I add to spliced array element for every sublevel and `concat` it with original array.
     *
     * @param {Object} restore - Object holding reference to `mergedVertical` object.
     * @param {String} levelId - level ID as string.
     * @param {Object} obs - Recalculated observations.
     * @param {String} course - course ID as string.
     * @param {Integer} i - Sublevel index.
     * @param {Integer} j - Student index.
     */
    function addSublevelsToVerticalRestore(restore, levelId, obs, course, i, j) {
        restore[j].cells = Array.from(restore[j].cells);
        
        const elem = restore[j].cells
            .filter(elem => $(elem).hasClass(`level-${levelId}`));

        const index = restore[j].cells.indexOf(elem[0]);
        var splicedArray = restore[j].cells.splice(0, index + parseInt(i) + 1);

        splicedArray.push(createNewRestoreCell(obs[i], course, j));
        restore[j].cells = splicedArray.concat(restore[j].cells);
    }

    /**
     * Create new td element for every observation and student in sublevel inside `obs`.
     *
     * @param {Object} obs - Recalculated observations.
     * @param {String} course - One of merged courses.
     * @param {Integer} j - Student index inside `obs[j]` array.
     */
    function createNewRestoreCell(obs, course, j) {
        var element = $(document.createElement('td'));

        // If any observations were created for student create element with star
        // otherwise create empty element.
        if (obs[j].length !== 0) {
            // If last student in class add thicker class.
            if (obs.length - 1 === j) {
                element = $(element[0])
                    .addClass('text-center thicker')
                    .append(addTooltip())
                    .append(createSpan(obs[j]));
            } else {
                element = $(element[0])
                    .addClass('text-center')
                    .append(addTooltip())
                    .append(createSpan(obs[j]));
            }

            element[0].dataset.cslId = "";
            element[0].dataset.modalLaunchObservations = `[${obs[j]}]`;
            element[0].dataset.class = course;
        } else {
            var element = null;

            // If last student in class add thicker class.
            if (obs.length - 1 === j) {
                element = $(element[0])
                    .addClass('text-center thicker');
            } else {
                element = $(element[0])
                    .addClass('text-center');
            }
                        
            element[0].dataset.cslId = "";
            element[0].dataset.class = course;
            element[0].dataset.modalLaunchObservations = "";
        }

        return element[0];
    }

    /**
     * Remove level element in `mergedVertical` object for every student in merged courses.
     *
     * @param {Array} mergedCourses - ID of merged courses per construct. 
     * @param {Object} observations - ID's of observations per course and per student for merged courses.
     * @param {String} constructId - ID of construct as string.
     * @param {String} levelId - ID of level as string
     */
    function removeLevelElement(mergedCourses, observations, constructId, levelId) {
        mergedCourses.forEach((course) => {
            var restore = mergedVertical[constructId][course];
            var obs = observations[course];

            Object.keys(obs).forEach(i => {
                for (j = 0; j < obs[i].length; j++) {
                    restore[j].cells = Array.from(restore[j].cells);
                    const elem = restore[j].cells
                        .filter(elem => $(elem).hasClass(`level-${levelId}`));

                    const index = restore[j].cells.indexOf(elem[0]);

                    if (index !== -1) {
                        restore[j].cells.splice(index, 1);
                    }
                }
            })
        })
    }

    $('.horizontal-unmerge').hide();

    $('.class-separate').hide();

    $('.horizontal-merge').click(function() {
        var isLast = false;

        const levelId = $(this).attr('id').split('-')[1];
        const sublevelsAmount = $(this).data('sublevels');
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const levelName = $(this).data('level-name');
        const levelCount = $(this).data('levels-count');

        // No reason to merge when only one sublevel is used.
        if (sublevelsAmount > 1) {
            // Get all headers for level.
            var headers = getAllHeaders(constructId, levelId);

            // Hide tooltips for merged headers.
            [...Array(headers.length).keys()].map(i => $(headers[i]).tooltip("hide"));

            mergedHorizontalLevels[levelId] = {
                'headers': headers,
                'cells': getCells(headers, constructId, construct)
            };

            // Check if merged sublevels are inside last level in table.
            isLast = isLastLevel(constructId, construct, headers, levelCount);
            headers.remove();

            // Get first <th> element for specific table.
            var header = $(`.star_chart_table-${constructId} tr:eq(1)`).first();

            // If merged level is last inside table I have to add new header after the last element which left.
            // Otherwise add new header before sublevel which was first inside table before removing it.
            if (isLast) {
                addHeaderAfter(header, startIndex - 2, levelId, levelName);
            } else {
                addHeaderBefore(header, startIndex - 1, levelId, levelName);
            }

            const cells = mergedHorizontalLevels[levelId].cells;

            // Initialize dictionary with amout of observations per cell.
            var starAmount = calculateStarAmount(cells);

            // Gets tds which are end of class.
            endClasses = getTdsWhichEndClass(cells);

            // Adds new <td>'s to table.
            [...Array(cells[0].length).keys()].map(
                i => addColumn(starAmount[i], startIndex, constructId, i, isLast, levelId));

            // Change colspan of parent th element to 1.
            $(this).parent().attr('colspan', 1);
            $(this).hide();
            $(`#horizontal-back-${levelId}`).show();

            mergedLevels[constructId].push(levelId);
        }
    })

    $('.horizontal-unmerge').click(function() {
        const levelId = $(this).attr('id').split('-')[2];
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const levelCount = $(this).data('levels-count');

        var header = $(`.star_chart_table-${constructId} tr`)
            .find(`[data-level-id='${levelId}']`);

        var isLast = isLastLevel(constructId, construct, header, levelCount);
        findCells(header, 0, constructId, construct).remove();
        header.remove();

        // Get observations and headers which were merged for current levelId.
        var cells = mergedHorizontalLevels[levelId].cells;
        const headers = mergedHorizontalLevels[levelId].headers;
        const mergedCourses = mergingStatus[constructId];

        var newCells = cells;

        if (mergedCourses.length !== 0) {
            newCells = createNewCellsToRestore(mergedCourses, levelId);
        }

        // Restore merged columns.
        for (var i = headers.length - 1; i >= 0; i--) {
            restoreSublevelHeader(isLast, constructId, headers[i]);

            for (var j = 0; j < cells[i].length; j++) {
                restoreSublevelCell(isLast, constructId, newCells[i][j], j + 2);
            }
        }

        let parent = $(this).parent();
        parent.attr('colspan', parent.data('sublevels'));

        $(this).hide();
        $(`#horizontal-${levelId}`).show();

        remakeTooltips();

        // Update vertical object when any class in construct is merged.
        if (mergedCourses.length !== 0) {
            // Get id's of observations for every student in merged classes.
            var newObservations = recalculateHorizontal(mergedCourses, cells);

            // Update `mergedVertical` with new elements containing recalculated observations. 
            updateVerticalRestore(mergedCourses, levelId, constructId, newObservations);

            // Remove level element for students in `mergedVertical` object.
            removeLevelElement(mergedCourses, newObservations, constructId, levelId);
        }

        mergedHorizontalLevels[levelId] = {};

        var index = mergedLevels[constructId].indexOf(levelId);

        if (index > -1) {
            mergedLevels[constructId].splice(index, 1);
        }
    })

    /**
     * Calculates quantity of observations for each sublevel inside merging class.
     * @param {Integer} sublevels - Amount of sublevels used in single table.
     * @param {Integer} constructId - Table's construct ID.
     * @param {Integer} classId - Merging class ID.
     */
    function calculateStarAmountVerticalByLevel(sublevels, constructId, classId) {
        var starAmount = [];

        for (var i = 0; i < sublevels; i++) {
            starAmount.push([]);
        }

        var size = mergedVertical[constructId][classId].length;

        for (var i = 0; i < size; i++) {
            for (var j = 0; j < sublevels; j++) {
                const observations = $(mergedVertical[constructId][classId][i].cells[j]).data('modal-launch-observations');
                
                if (observations) {
                    // Add observations and filter reoccurring ones.
                    observations.forEach(observation => {
                        if (!starAmount[j].some(star => observation === star)) {
                            starAmount[j].push(observation);
                        }
                    });
                }

                $(mergedVertical[constructId][classId][i].student).remove();
                $(mergedVertical[constructId][classId][i].cells[j]).remove();
            }
        }

        return starAmount;
    }

    /**
     * Saves students and stars cells for merging class to restore them later
     * when separate button is clicked.
     * Cells are saved in this way:
     * {
     *   "student": Selector - <th> selector with student name.
     *   "cells": [] - Array with <td> cells for stars.
     * }
     * @param {Array} students - <th> elements with students names.
     * @param {Integer} constructId - ID of construct.
     * @param {Integer} classId - ID of merging class. 
     */
    function saveCells(students, constructId, classId) {
        var sublevels = 0;

        if (!mergedVertical.hasOwnProperty(constructId)) {
            mergedVertical[constructId] = {};
        }

        mergedVertical[constructId][classId] = []

        for (var i = 0; i < students.length; i++) {
            var cells = $($(students[i]).parent()).find('td');
            sublevels = cells.length;
            mergedVertical[constructId][classId].push({'student': students[i], 'cells': cells});
        }

        return sublevels;
    }

    $('.class-merge').click(function() {
        const className = $(this).data('class');
        const classId = $(this).attr('id').split('-')[2];
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];

        // Get <th> elements for students.
        var students = $(`.star_chart_table-${constructId} tr`).find(`.class-${classId}`);

        // Save cells to restore them when separating class.
        const sublevels = saveCells(students, constructId, classId);

        // Calculate amount of stars for each level inside merging class.
        const starAmount = calculateStarAmountVerticalByLevel(sublevels, constructId, classId);

        // Remove all empty <th> elements which starts row.
        $(`.star_chart_table-${constructId}`).find(`.class-${classId}`).remove();

        var tr = $(this).parent().parent();

        // Append <th> with `className` to row which left.
        $(tr).append(`<th scope="row" class="student-${constructId} class-${classId}
            thicker student-cell">${className}</th>`);

        // Append to last row of class all stars for each level.
        for (var i = 0; i < sublevels; i++) {
            if (starAmount[i].length !== 0) {
                let span = createSpan(starAmount[i]);

                $(tr).append(`<td data-csl-id="" class="text-center thicker"
                    data-modal-launch-observations="[${starAmount[i]}]">
                    ${addTooltip()}${span}</td>`);
            } else {
                $(tr).append('<td data-csl-id="" class="text-center thicker"></td>');
            }
        }

        $(this).hide();
        $(`#class-separate-${classId}-${constructId}`).show();

        mergingStatus[constructId].push(classId);
    })

    $('.class-separate').click(function() {
        const classId = $(this).attr('id').split('-')[2];
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];

        const levels = [...mergedLevels[constructId]];

        if (levels.length !== 0) {
            // Trigger only one case to update objects in one way.
            levels.forEach(level => $(`#horizontal-back-${level}`).trigger('click'));
            $(this).trigger('click');
            levels.forEach(level => $(`#horizontal-${level}`).trigger('click'));
        } else {
            var tr = $(this).parent().parent();
            var size = mergedVertical[constructId][classId].length;
            var cells = $(tr).find('td');

            // Get amount of sublevels used in table.
            const sublevels = cells.length;

            // Remove all <td> elements inside created earlier row.
            cells.remove();

            // Remove header with class name
            $(tr).find('th:eq(1)').remove();

            // Append to row with button header with first student <th> element.
            $(tr).append(mergedVertical[constructId][classId][size - 1].student);

            // Append saved <td>s elements to row.
            [...Array(sublevels).keys()].forEach(
                i => $(tr).append(mergedVertical[constructId][classId][size - 1].cells[i]));

            // Create new rows and append saved information about students.
            for (var i = size - 2; i >= 0; i--) {
                $(tr).before(`<tr class="construct-${constructId} class-${classId}"></tr>`);
                tr = $(tr).prev();
                $(tr).append('<th scope="col">&nbsp;</th>');
                $(tr).append(mergedVertical[constructId][classId][i].student);

                // Append saved <td>s elements to row.
                [...Array(sublevels).keys()].forEach(
                    j => $(tr).append(mergedVertical[constructId][classId][i].cells[j]));
            }

            $(this).hide();
            $(`#class-merge-${classId}-${constructId}`).show();

            // Remove class from mergingStatus inside construct.
            var index = mergingStatus[constructId].indexOf(classId);

            if (index > -1) {
                mergingStatus[constructId].splice(index, 1);
            }
        }
    })
})()
