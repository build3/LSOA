(() => {
    // Horizontal sublevels which were merged.
    var mergedHorizontalLevels = {};

    // Describes in what position new elements are added to table.
    var startIndex = 0;

    var endClasses = [];

    /**
     * Adds new column to table.
     * @param {Array} star_amount - Amount of observation per student.
     * @param {Integer} startIndex - Position inside table where new elements are created.
     * @param {Integer} constructId - ID of construct
     * @param {Integer} i - Index element.
     * @param {Boolean} isLast - Describes if level was last in table.
     */
    function addColumn(star_amount, startIndex, constructId, i, isLast) {
        if (star_amount.length !== 0) {
            addColumnWithStar(startIndex, constructId, star_amount, i, isLast)
        } else if (isLast) {
            addEmptyCellAfter(constructId, i + 1, startIndex - 2)
        } else {
            addEmptyCellBefore(constructId, i + 1, startIndex - 1);
        }
    }

    function addColumnWithStar(startIndex, constructId, stars, rowIndex, isLast) {
        let span = createSpan(stars);

        if (isLast) {
            starColumnAfter(rowIndex + 1, constructId, startIndex - 2, stars, span);
        } else {
            starColumnBefore(rowIndex + 1, constructId, startIndex - 1, stars, span);
        }
    }

    /**
     * Check if level is last inside table.
     * Level is last when sum of his `startIndex` and `<th>` elements is
     * equal to all headers inside table - cells for students name(Those are maked with <th> too)
     * and - count of levels for construct.
     * @param {Integer} constructId 
     * @param {String} construct 
     * @param {Array} headers 
     */
    function isLastLevel(constructId, construct, headers, levelCount) {
        const cellIndex = headers[0].cellIndex;

        const cells = $(`.star_chart_table-${constructId} .${construct}`)
            .find(`td:eq(0)`);
        startIndex = cellIndex;
        const allHeaders = $(`.star_chart_table-${constructId}`)
            .find('th');
    
        return startIndex + (headers.length) === allHeaders.length - cells.length - levelCount - 1
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
     * Generate header when separating merged level.
     * @param {Object} star 
     * @param {Integer} levelId 
     */
    function genareteHeader(star, levelId) {
        return `<th scope="col" style="text-align:center;" class="align-middle" ` +
            `title="${star.description}" data-toggle="tooltip" data-level-id="${levelId}">${star.name}</th>`
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
    function removeColumns(headers, i, constructId, construct) {
        const cellIndex = headers[i].cellIndex;

        if (i == 0) {
            startIndex = cellIndex;
        }
                
        const cells = $(`.star_chart_table-${constructId} .${construct}`)
            .find(`td:eq(${cellIndex - 1})`);
        
        const value = cells;

        headers[i].remove();
        cells.remove();

        return value;
    }

    /**
     * Get sublevel data from one of <th> elements.
     * @param {Selector} header - One of <th> element. 
     */
    function getSublevelData(header) {
        return {
            'name': header.innerHTML,
            'description': header.dataset.originalTitle
        }
    }

    function addEmptyCellBefore(constructId, j, startIndex) {
        var element = $(document.createElement('td'))
            .addClass('text-center');
        element[0].dataset.cslId = "";

        if (endClasses.includes(j - 1)) {
            $(element[0]).css('border-bottom', '3pt solid black').addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${j + 1})`)
            .find(`td`)
            .eq(startIndex)
            .before(element[0]);
    }

    function addEmptyCellAfter(constructId, j, startIndex) {
        var element = $(document.createElement('td'))
            .addClass('text-center');
        element[0].dataset.cslId = "";

        if (endClasses.includes(j - 1)) {
            $(element[0]).css('border-bottom', '3pt solid black').addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${j + 1})`)
            .find(`td`)
            .eq(startIndex)
            .after(element[0]);
    }

    function starColumnBefore(rowIndex, constructId, startIndex, stars, span) {
        var element = $(document.createElement('td'))
            .addClass('text-center')
            .append('<i data-toggle="tooltip" title="" class="fa fa-star"></i>')
            .append(span);

        element[0].dataset.cslId = "";
        element[0].dataset.modalLaunchObservations = `[${stars}]`;

        if (endClasses.includes(rowIndex - 1)) {
            $(element[0]).css('border-bottom', '3pt solid black').addClass("thicker");
        }

        $(`.star_chart_table-${constructId}`)
            .find(`tr:eq(${rowIndex + 1})`)
            .find('td')
            .eq(startIndex)
            .before(element[0]);
    }

    function starColumnAfter(rowIndex, constructId, startIndex, stars, span) {
        var element = $(document.createElement('td'))
            .addClass('text-center')
            .append('<i data-toggle="tooltip" title="" class="fa fa-star"></i>')
            .append(span);

        element[0].dataset.cslId = "";
        element[0].dataset.modalLaunchObservations = `[${stars}]`;

        if (endClasses.includes(rowIndex - 1)) {
            $(element[0]).css('border-bottom', '3pt solid black').addClass("thicker");
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
            .eq(startIndex)
            .after(`<th style="text-align:center;" class="align-middle" ` +
                `scope="col" data-toggle="tooltip" data-level-id="${levelId}">${levelName}</th>`);
    }

    function addHeaderBefore(header, startIndex, levelId, levelName) {
        $(header)
            .find('th')
            .eq(startIndex)
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
    function calculate_star_amount(stars) {
        var star_amount = {}

        for (var i = 0; i < stars[0].length; i++) {
            star_amount[i] = []

            for (var j = 0; j < stars.length; j++) {
                const observations = $(stars[j][i]).data('modal-launch-observations');
                
                if (observations) {
                    // Add observations and filter reoccurring ones.
                    observations.map(observation => {
                        if (!star_amount[i].some(star => observation === star)) {
                            star_amount[i].push(observation);
                        }
                    });
                }
            }
        }

        return star_amount;
    }

    /**
     * Adds merged observations to `mergedHorizontalLevels`.
     * @param {Array} stars - Array with <td> elements. 
     * @param {Integer} levelId 
     */
    function addMergedLevel(stars, levelId) {
        for (var i = 0; i < stars.length; i++) {
            for (var j = 0; j < stars[0].length; j++) {
                mergedHorizontalLevels[levelId][i][j + 1] = [];
                const observations = $(stars[i][j]).data('modal-launch-observations');
                
                if (observations) {
                    observations.map(observation =>
                        mergedHorizontalLevels[levelId][i][j + 1].push(observation));
                }
            }
        }
    }

    /**
     * Initializes `mergedHorizontalLevels`.
     * @param {Integer} levelId
     * @param {Integer} i - Index from loop.
     * @param {Array} headers - Array with <th> for specific level.
     */
    function initMergedLevel(levelId, i, headers) {
        mergedHorizontalLevels[levelId][i] = {};
        mergedHorizontalLevels[levelId][i][0] = getSublevelData(headers[i]);
    }

    /**
     * Add cells which are inside sublevels columns to `stars` array then remove
     * those columns and calculate `startIndex`.
     * In addition each sublevel and his observations
     * are added to mergedHorizontalLevels dictionary.
     */
    function getCells(headers, levelId, constructId, construct) {
        var stars = [];

        [...Array(headers.length).keys()].map(i => {
            initMergedLevel(levelId, i, headers);
            stars[i] = removeColumns(headers, i, constructId, construct);
        });

        return stars;
    }

    /**
     * Insert back merged columns.
     * @param {Integer} sublevelsAmount
     * @param {boolean} isLast
     * @param {Integer} constructId
     * @param {Integer} levelId
     * @param {Array} stars
     * @param {Integer} startIndex
     */
    function insertMergedColumns(sublevelsAmount, isLast, constructId, levelId, stars, startIndex) {
        for (var i = sublevelsAmount - 1; i >= 0; i--) {
            if (isLast) {
                $($(`.star_chart_table-${constructId} tr:eq(1)`).first())
                    .find('th')
                    .eq(startIndex - 1)
                    .after(genareteHeader(stars[i][0], levelId));
            } else {
                $($(`.star_chart_table-${constructId} tr:eq(1)`).first())
                    .find('th')
                    .eq(startIndex)
                    .before(genareteHeader(stars[i][0], levelId));
            }

            for (var j = 1; j < Object.keys(stars[i]).length; j++) {
                if (stars[i][j].length !== 0) {
                    let span = createSpan(stars[i][j]);

                    if (isLast) {
                        starColumnAfter(j, constructId,
                            startIndex - sublevelsAmount + (sublevelsAmount - 2), stars[i][j], span);
                    } else {
                        starColumnBefore(j, constructId, startIndex - 1, stars[i][j], span);
                    }
                } else {
                    if (isLast) {
                        addEmptyCellAfter(constructId, j,
                            startIndex - sublevelsAmount + (sublevelsAmount - 2));
                    } else {
                        addEmptyCellBefore(constructId, j, startIndex - 1);
                    }
                }
            }
        }
    }

    function getTdsWhichEndClass(stars) {
        return [...Array(stars[0].length).keys()].filter(i => $(stars[0][i]).hasClass('thicker'));
    }

    $('.horizontal-unmerge').hide();

    $('.horizontal-merge').click(function() {
        var isLast = false;

        const levelId = $(this).attr('id').split('-')[1]
        const sublevelsAmount = $(this).data('sublevels');
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const levelName = $(this).data('level-name');
        const levelCount = $(this).data('levels-count');

        // No reason to merge when only one sublevel is used.
        if (sublevelsAmount > 1) {
            // Initialize mergedHorizontalLevels with level ID which is getting merge.
            mergedHorizontalLevels[levelId] = {};

            // Get all headers for level.
            var headers = getAllHeaders(constructId, levelId);

            // Check if merged sublevels are inside last level in table.
            isLast = isLastLevel(constructId, construct, headers, levelCount);
            var stars = getCells(headers, levelId, constructId, construct);

            // Get first <th> element for specific table.
            var header = $(`.star_chart_table-${constructId} tr:eq(1)`).first();

            // If merged level is last inside table I have to add new header after the last element which left.
            // Otherwise add new header before sublevel which was first inside table before removing it.
            if (isLast) {
                addHeaderAfter(header, startIndex - 1, levelId, levelName);
            } else {
                addHeaderBefore(header, startIndex, levelId, levelName);
            }

            // Initialize dictionary with amout of observations per cell.
            var star_amount = calculate_star_amount(stars);

            // Gets tds which are end of class.
            endClasses = getTdsWhichEndClass(stars);

            // Add observations to `mergedHorizontalLevels` including all observations.
            addMergedLevel(stars, levelId);

            // Adds new <td>'s to table.
            [...Array(stars[0].length).keys()].map(
                i => addColumn(star_amount[i], startIndex, constructId, i, isLast));

            // Change colspan of parent th element to 1.
            $(this).parent().attr('colspan', 1);
            $(this).hide();
            $(`#horizontal-back-${levelId}`).show();
        }
    })

    $('.horizontal-unmerge').click(function() {
        const levelId = $(this).attr('id').split('-')[2]
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const sublevelsAmount = $(this).data('sublevels');
        const levelCount = $(this).data('levels-count');

        var header = $(`.star_chart_table-${constructId} tr`)
            .find(`[data-level-id='${levelId}']`);

        var isLast = isLastLevel(constructId, construct, header, levelCount);
        removeColumns(header, 0, constructId, construct);

        // Get observations which were merged for current levelId.
        const stars = mergedHorizontalLevels[levelId];

        // Creates new columns with observations which were there before merge.
        insertMergedColumns(sublevelsAmount, isLast, constructId, levelId, stars, startIndex);

        mergedHorizontalLevels[levelId] = {}

        let parent = $(this).parent();
        parent.attr('colspan', parent.data('sublevels'));

        $(this).hide();
        $(`#horizontal-${levelId}`).show();

        remakeTooltips();
    })
})()
