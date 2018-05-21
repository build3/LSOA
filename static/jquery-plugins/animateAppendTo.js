$.fn.animateAppendTo = function(sel, speed, callback) {
    callback = callback || function(){};
    speed = speed || 500;
    var $this = this,
        newEle = $($this.outerHTML()).appendTo(sel),
        newPos = newEle.position(),
        curPos = $this.offset();

    newEle.hide();
    $this.appendTo('body').css({position: 'absolute', top: curPos.top, left: curPos.left}).animate(newPos, speed, function() {
        newEle.show();
        $this.remove();
        callback(newEle);
    });
    return newEle;
};
