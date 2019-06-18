/**
 * This file contains merge ability for star chart v4.
 */

(() => {
    // Merged horizontal columns.
    var horizontalStarChart4 = {};
    var startIndex = 0;

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
     * Get sublevel data from one of <th> elements.
     * @param {Selector} header - One of <th> element. 
     */
    function getSublevelData(header) {
        return {
            'name': header.innerHTML,
            'description': header.dataset.originalTitle
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

    function initMergedLevel4(levelId, i, headers) {
        horizontalStarChart4[levelId][i] = {};
        horizontalStarChart4[levelId][i][0] = getSublevelData(headers[i]);
    }

    /**
     * Removes and returns columns which are merged in addition sets startIndex.
     * @param {Array} headers 
     * @param {Integer} i 
     * @param {Integer} constructId 
     * @param {String} construct 
     */
    function removeColumns4(headers, i, constructId, construct) {
        const cellIndex = headers[i].cellIndex;

        if (i == 0) {
            startIndex = cellIndex;
        }

        const cells = $(`.star-chart-4-table-${constructId} .${construct}`)
            .find(`td:eq(${cellIndex})`);

        const value = cells;

        headers[i].remove();
        cells.remove();

        return value;
    }

    /**
     * Gets cells for merged level.
     * @param {Array} headers 
     * @param {Integer} levelId 
     * @param {Integer} constructId 
     * @param {String} construct 
     */
    function getCells4(headers, levelId, constructId, construct) {
        var stars = [];
    
        [...Array(headers.length).keys()].map(i => {
            initMergedLevel4(levelId, i, headers);
            stars[i] = removeColumns4(headers, i, constructId, construct);
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

        return startIndex + (headers.length) === allHeaders.length - levelCount
    }

    /**
     * Calculates amount of stars after merge.
     * @param {Array} stars 
     */
    function calculateStars4(stars) {
        var amount = 0;

        for (var i = 0; i < stars.length; i++) {
            amount += [...Array(stars[0].length).keys()].reduce((acc, val) => {
                const observations = $(stars[i][val]).data('stars');
                return acc += observations === undefined ? 0 : observations;
            }, 0)
        }

        return amount
    }

    /**
     * Creates and returns array with color and amount of stars for merged cells.
     * @param {Array} stars
     */
    function calculateStarsAndColors4(stars) {
        var star_amount = {}
    
        for (var i = 0; i < stars.length; i++) {
            star_amount[i] = {}

            for (var j = 0; j < stars[0].length; j++) {
                const observations = $(stars[i][j]).data('stars');
                const color = $(stars[i][j]).data('color');

                star_amount[i].observations = observations === undefined ? 0 : observations;

                if (color) {
                    star_amount[i].color = color;
                }
            }
        }
    
        return star_amount;
    }

    /**
     * Add cells for merged level to `horizontalStarChart4` object.
     * @param {Array} stars 
     * @param {Integer} levelId 
     */
    function addMergedLevel4(stars, levelId) {
        const star_colors = calculateStarsAndColors4(stars)

        for (var i = 0; i < stars.length; i++) {
            horizontalStarChart4[levelId][i][1] = star_colors[i];
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
    function calculateNewColor4(starAmount, constructId) {
        if (starAmount == 0) {
            return window.COLORS_DARK["0"];
        }

        const cells = $(`.star-chart-4-table-${constructId}`).find('.stars-amount');
        const allStars = [...Array(cells.length).keys()].reduce(
            (acc, val) => acc += $(cells[val]).data('stars'), starAmount);

        const percentValue = 100 * starAmount / allStars;

        if (percentValue < 10) {
            return window.COLORS_DARK["LESS_THEN_10"]
        } else {
            return window.COLORS_DARK[percentValue.toString()[0]]
        }
    }

    function addColumn4(startIndex, starAmount, newColor, isLast, constructId) {
        const colorsRow = 2;
        const starsRow = 3;

        var heatMapElement = $(document.createElement('td'))
            .addClass('text-center')
            .attr('bgcolor', newColor);

        heatMapElement[0].dataset.cslId = "";
        heatMapElement[0].dataset.color = newColor;

        var starElement = $(document.createElement('td'))
            .addClass('text-center stars-amount')
            .append(`<span>${starAmount}</span>`);

        starElement[0].dataset.cslId = "";
        starElement[0].dataset.stars = starAmount;

        if (isLast) {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${colorsRow})`)
                .find('td')
                .eq(startIndex - 1)
                .after(heatMapElement[0]);

            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${starsRow})`)
                .find('td')
                .eq(startIndex - 1)
                .after(starElement[0]);
        } else {
            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${colorsRow})`)
                .find('td')
                .eq(startIndex)
                .before(heatMapElement[0]);

            $(`.star-chart-4-table-${constructId}`)
                .find(`tr:eq(${starsRow})`)
                .find('td')
                .eq(startIndex)
                .before(starElement[0]);
        }
    }

    function insertMergedColumns4(sublevelsAmount, isLast, constructId, levelId, stars, startIndex) {
        for (var i = sublevelsAmount - 1; i >= 0; i--) {
            if (isLast) {
                $($(`.star-chart-4-table-${constructId} tr:eq(1)`).first())
                    .find('th')
                    .eq(startIndex - 1)
                    .after(genareteHeader(stars[i][0], levelId));
            } else {
                $($(`.star-chart-4-table-${constructId} tr:eq(1)`).first())
                    .find('th')
                    .eq(startIndex)
                    .before(genareteHeader(stars[i][0], levelId));
            }

            addColumn4(startIndex, stars[i][1].observations,
                stars[i][1].color, isLast, constructId)
        }
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
            // Initialize mergedHorizontalLevels with level ID which is getting merge.
            horizontalStarChart4[levelId] = {};

            // Get all headers for level.
            var headers = getAllHeaders4(constructId, levelId);

            // Hide tooltips for merged headers.
            [...Array(headers.length).keys()].forEach(i => $(headers[i]).tooltip("hide"));

            // Check if merged sublevels are inside last level in table.
            isLast = isLastLevel4(constructId, construct, headers, levelCount);
            var stars = getCells4(headers, levelId, constructId, construct);

            // Get first <th> element for specific table.
            var header = $(`.star-chart-4-table-${constructId} tr:eq(1)`).first();

            // If merged level is last inside table I have to add new header after the last element which left.
            // Otherwise add new header before sublevel which was first inside table before removing it.
            if (isLast) {
                addHeaderAfter(header, startIndex - 2, levelId, levelName);
            } else {
                addHeaderBefore(header, startIndex - 1, levelId, levelName);
            }

            // Initialize dictionary with amout of observations per cell.
            var starAmount = calculateStars4(stars);
            var newColor = calculateNewColor4(starAmount, constructId);

            // Add observations to `mergedHorizontalLevels` including all observations.
            addMergedLevel4(stars, levelId);
            addColumn4(startIndex, starAmount, newColor, isLast, constructId)

            // Change colspan of parent th element to 1.
            $(this).parent().attr('colspan', 1);
            $(this).hide();
            $(`#horizontal-back-4-${levelId}`).show();
        }
    })

    $('.horizontal-unmerge-4').click(function() {
        const levelId = $(this).attr('id').split('-')[3]
        const construct = $(this).data('construct');
        const constructId = construct.split('-')[1];
        const sublevelsAmount = $(this).data('sublevels');
        const levelCount = $(this).data('levels-count');

        var header = $(`.star-chart-4-table-${constructId} tr:eq(1)`)
            .find(`[data-level-id="${levelId}"]`);

        var isLast = isLastLevel4(constructId, construct, header, levelCount);
        removeColumns4(header, 0, constructId, construct);

        // Get observations which were merged for current levelId.
        const stars = horizontalStarChart4[levelId];

        // Creates new columns with observations which were there before merge.
        insertMergedColumns4(sublevelsAmount, isLast, constructId, levelId, stars, startIndex);

        horizontalStarChart4[levelId] = {}

        let parent = $(this).parent();
        parent.attr('colspan', parent.data('sublevels'));

        $(this).hide();
        $(`#horizontal-4-${levelId}`).show();

        remakeTooltips();
    })
})()
