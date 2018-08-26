
// This modifies the layout of Django's standard datetime widget so that date and time appear on same line.
// It finds the <br>s between date and time and replaces them with inline-block spacers.

window.addEventListener(
    "load",
    function() {
        var dtbrs = document.evaluate("//p[@class='datetime']/br", document.body,null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        for (var i=0; i<dtbrs.snapshotLength; i++) {

            var spacer = document.createElement("div");
            var spacerClass = document.createAttribute("class");
            spacerClass.value = "datetimespacer";
            spacer.setAttributeNode(spacerClass);

            var dtbr = dtbrs.snapshotItem(i);
            dtbr.parentNode.replaceChild(spacer, dtbr);
        }
    }
);