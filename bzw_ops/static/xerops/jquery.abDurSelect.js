/**
 * FILE: jQuery.abDurSelect.js
 *  
 * @fileOverview
 * jQuery plugin for displaying a popup that allows a user
 * to define a duration and set that duration back to a form's input
 * field. This is a modification of Paul Tavares' abDurSelect.
 * 
 * @requires jQuery {@link http://www.jquery.com}
 * 
 * 
 * INSTALLATION:
 * 
 * There are two files (.css and .js) delivered with this plugin and
 * that must be included in your html page after the jquery.js library
 * and the jQuery UI style sheet (the jQuery UI javascript library is
 * not necessary).
 * Both of these are to be included inside of the 'head' element of
 * the document. Example below demonstrates this along side the jQuery
 * libraries.
 * 
 * |    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
 * |    <link rel="stylesheet" type="text/css" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.22/themes/redmond/jquery-ui.css" />
 * |
 * |    <link rel="stylesheet" type="text/css" href="jquery.abDurSelect.css" />
 * |    <script type="text/javascript" src="jquery.abDurSelect.js"></script>
 * |
 * 
 * USAGE:
 * 
 *     -    See <$(ele).abDurSelect()>
 * 
 * 
 * 
 * LAST UPDATED:
 * 
 *         - $Date: 2012/08/05 19:40:21 $
 *         - $Author: paulinho4u $
 *         - $Revision: 1.8 $
 * 
 */

(function($){
    
    /**
     *  jQuery definition
     *
     *  @see    http://jquery.com/
     *  @name   jQuery
     *  @class  jQuery Library
     */
    
    /**
     * jQuery 'fn' definition to anchor all public plugin methods.
     * 
     * @see         http://jquery.com/
     * @name        fn
     * @class       jQuery Library public method anchor
     * @memberOf    jQuery
     */
    
    /**
     *  Namespace for all properties and methods
     *  
     *  @namespace   abDurSelect
     *  @memberOf    jQuery
     */
    jQuery.abDurSelect         = {};
    jQuery.abDurSelect.version = "__BUILD_VERSION_NUMBER__";
    
    /**
     * The default options for all calls to abDurSelect. Can be
     * overwriten with each individual call to {@link jQuery.fn.abDurSelect}
     *  
     * @type {Object} options
     * @memberOf jQuery.abDurSelect
     * @see jQuery.fn.abDurSelect
     */
    jQuery.abDurSelect.options = {
        containerClass: undefined,
        containerWidth: '13em',
        hoursLabel:     'Hours',
        minutesLabel:   'Mins',
        setButtonLabel: 'Set',
        popupImage:     undefined,
        onFocusDisplay: true,
        zIndex:         10,
        onBeforeShow:   undefined,
        onClose:        undefined
    };
    
    /**
     * Internal method. Called when page is initialized to add the time
     * selection area to the DOM.
     *  
     * @private
     * @memberOf jQuery.abDurSelect
     * @return {undefined}
     */
    jQuery.abDurSelect._abDurSelectInit = function () {
        jQuery(document).ready(
            function () {
                //if the html is not yet created in the document, then do it now
                if (!jQuery('#abDurSelectCntr').length) {
                    jQuery("body").append(
                            '<div id="abDurSelectCntr" class="">'
                        +    '        <div class="ui-widget ui-widget-content ui-corner-all">'
                        +    '        <div class="ui-widget-header ui-corner-all">'
                        +    '            <div id="abDurSelectCloseCntr" style="float: right;">'
                        +    '                <a href="javascript: void(0);" onclick="jQuery.abDurSelect.closeCntr();" '
                        +    '                        onmouseover="jQuery(this).removeClass(\'ui-state-default\').addClass(\'ui-state-hover\');" '
                        +    '                        onmouseout="jQuery(this).removeClass(\'ui-state-hover\').addClass(\'ui-state-default\');"'
                        +    '                        class="ui-corner-all ui-state-default">'
                        +    '                    <span class="ui-icon ui-icon-circle-close">X</span>'
                        +    '                </a>'
                        +    '            </div>'
                        +    '            <div id="abDurSelectUserTime" style="float: left;">'
                        +    '                <span id="abDurSelectUserSelHr">1</span> : '
                        +    '                <span id="abDurSelectUserSelMin">00</span> '
                        +    '                <span id="abDurSelectUserSelAmPm">AM</span>'
                        +    '            </div>'
                        +    '            <br style="clear: both;" /><div></div>'
                        +    '        </div>'
                        +    '        <div class="ui-widget-content ui-corner-all">'
                        +    '            <div>'
                        +    '                <div class="abDurSelectTimeLabelsCntr">'
                        +    '                    <div class="abDurSelectLeftPane" style="width: 70%; text-align: center; float: left;" class="">Hour</div>'
                        +    '                    <div class="abDurSelectRightPane" style="width: 30%; text-align: center; float: left;">Minutes</div>'
                        +    '                </div>'
                        +    '                <div>'
                        +    '                    <div style="float: left; width: 70%;">'
                        +    '                        <div class="ui-widget-content abDurSelectLeftPane">'
                        +    '                            <div class="abDurSelectHrCntr">'
                        +    '                                <a class="abDurSelectHr ui-state-default" href="javascript: void(0);">1</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">2</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">3</a>'
                        +    '                                <br/>'
                        +    '                                <a class="abDurSelectHr ui-state-default" href="javascript: void(0);">4</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">5</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">6</a>'
                        +    '                                <br/>'
                        +    '                                <a class="abDurSelectHr ui-state-default" href="javascript: void(0);">7</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">8</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">9</a>'
                        +    '                                <br/>'
                        +    '                                <a class="abDurSelectHr ui-state-default" href="javascript: void(0);">10</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">11</a><!--'
                        +    '                             --><a class="abDurSelectHr ui-state-default" href="javascript: void(0);">12</a>'
                        +    '                                <br/>'
                        +    '                            </div>'
                        +    '                        </div>'
                        +    '                    </div>'
                        +    '                    <div style="width: 30%; float: left;">'
                        +    '                        <div class="ui-widget-content abDurSelectRightPane">'
                        +    '                            <div class="abDurSelectMinCntr">'
                        +    '                                <a class="abDurSelectMin ui-state-default" href="javascript: void(0);">00</a><!--'
                        +    '                             --><br/>'
                        +    '                                <a class="abDurSelectMin ui-state-default" href="javascript: void(0);">15</a><!--'
                        +    '                             --><br/>'
                        +    '                                <a class="abDurSelectMin ui-state-default" href="javascript: void(0);">30</a><!--'
                        +    '                             --><br/>'
                        +    '                                <a class="abDurSelectMin ui-state-default" href="javascript: void(0);">45</a><!--'
                        +    '                             --><br/>'
                        +    '                            </div>'
                        +    '                        </div>'
                        +    '                    </div>'
                        +    '                </div>'
                        +    '            </div>'
                        +    '            <div style="clear: left;"></div>'
                        +    '        </div>'
                        +    '        <div id="abDurSelectSetButton">'
                        +    '            <a href="javascript: void(0);" onclick="jQuery.abDurSelect.setTime()"'
                        +    '                    onmouseover="jQuery(this).removeClass(\'ui-state-default\').addClass(\'ui-state-hover\');" '
                        +    '                        onmouseout="jQuery(this).removeClass(\'ui-state-hover\').addClass(\'ui-state-default\');"'
                        +    '                        class="ui-corner-all ui-state-default" id="abDurSelectSetLink">'
                        +    '                SET'
                        +    '            </a>'
                        +    '        </div>'
                        +    '        <!--[if lte IE 6.5]>'
                        +    '            <iframe style="display:block; position:absolute;top: 0;left:0;z-index:-1;'
                        +    '                filter:Alpha(Opacity=\'0\');width:3000px;height:3000px"></iframe>'
                        +    '        <![endif]-->'
                        +    '    </div></div>'
                    );
                    
                    var e = jQuery('#abDurSelectCntr');
    
                    // Add the events to the functions
                    e.find('.abDurSelectMin')
                        .bind("click", function(){
                            jQuery.abDurSelect.setMinSelClass($(this))
                            jQuery.abDurSelect.setMin($(this).text());
                            jQuery(".isabDurSelectActive").focus();
                         });
                    
                    e.find('.abDurSelectHr')
                        .bind("click", function(){
                            jQuery.abDurSelect.setHrSelClass($(this))
                            jQuery.abDurSelect.setHr($(this).text());
                            jQuery(".isabDurSelectActive").focus();
                         });

                    $(document).mousedown(jQuery.abDurSelect._doCheckMouseClick);            
                }//end if
            }
        );
    }();// jQuery.abDurSelectInit()
    
    /**
     * Sets a class on the most recently clicked hour and removes the class
     * from the other hours. The class is used to color the most recently
     * selected hour.
     */
    jQuery.abDurSelect.setHrSelClass = function(h) {
        var highlightClass = 'abDurSelectLastClickedHr';
        jQuery('.'+highlightClass).removeClass(highlightClass);
        h.addClass(highlightClass);
    }

    /**
     * Sets a class on the most recently clicked minute and removes the class
     * from the other minutes. The class is used to color the most recently
     * selected minute.
     */
    jQuery.abDurSelect.setMinSelClass = function(m) {
        var highlightClass = 'abDurSelectLastClickedMin'
        jQuery('.'+highlightClass).removeClass(highlightClass);
        m.addClass(highlightClass);
    }


    /**
     * Sets the hour selected by the user on the popup.
     * 
     * @private 
     * @param  {Integer}   h   -   Interger indicating the hour. This value
     *                      is the same as the text value displayed on the
     *                      popup under the hour. This value can also be the
     *                      words AM or PM.
     * @return {undefined}
     * 
     */
    jQuery.abDurSelect.setHr = function(h) {
        jQuery('#abDurSelectUserSelHr').empty().append(h);
    };// END setHr() function
        
    /**
     * Sets the minutes selected by the user on the popup.
     * 
     * @private
     * @param {Integer}    m   - interger indicating the minutes. This
     *          value is the same as the text value displayed on the popup
     *          under the minutes.
     * @return {undefined}
     */
    jQuery.abDurSelect.setMin = function(m) {
        jQuery('#abDurSelectUserSelMin').empty().append(m);
    };// END setMin() function
        
    /**
     * Takes the time defined by the user and sets it to the input
     * element that the popup is currently opened for.
     * 
     * @private
     * @return {undefined}
     */
    jQuery.abDurSelect.setTime = function() {
        var hh = Number(jQuery('#abDurSelectUserSelHr').text());
        var mm = Number(jQuery('#abDurSelectUserSelMin').text());
        var tSel = hh + mm/60.0;
        jQuery(".isabDurSelectActive").val(tSel);
        this.closeCntr();
        
    };// END setTime() function
        
    /**
     * Displays the time definition area on the page, right below
     * the input field.  Also sets the custom colors/css on the
     * displayed area to what ever the input element options were
     * set with.
     * 
     * @private
     * @param {String} uId - Id of the element for whom the area will
     *                  be displayed. This ID was created when the 
     *                  abDurSelect() method was called.
     * @return {undefined}
     * 
     */
    jQuery.abDurSelect.openCntr = function (ele) {
        jQuery.abDurSelect.closeCntr();
        jQuery(".isabDurSelectActive").removeClass("isabDurSelectActive");
        var cntr            = jQuery("#abDurSelectCntr");
        var i               = jQuery(ele).eq(0).addClass("isabDurSelectActive");
        var opt             = i.data("abDurSelectOptions");
        var style           = i.offset();
        style['z-index']    = opt.zIndex;
        style.top           = (style.top + i.outerHeight());
        if (opt.containerWidth) {
            style.width = opt.containerWidth;
        }
        if (opt.containerClass) {
            cntr.addClass(opt.containerClass);
        }
        cntr.css(style);
        var hr    = 1;
        var min   = 0;
        var tm    = 'AM';
        if (i.val()) {
            hr = Math.floor(i.val());
            min = (i.val()-hr) * 60;
            jQuery.abDurSelect.setHrSelClass(
                jQuery("a.abDurSelectHr").filter(function(){return Number($(this).text())==hr;})
            )
            jQuery.abDurSelect.setMinSelClass(
                jQuery("a.abDurSelectMin").filter(function(){return Number($(this).text())==min;})
            )
        }
        cntr.find("#abDurSelectUserSelHr").empty().append(hr);
        cntr.find("#abDurSelectUserSelMin").empty().append(min);
        cntr.find("#abDurSelectUserSelAmPm").empty().append(tm);
        cntr.find(".abDurSelectTimeLabelsCntr .abDurSelectLeftPane")
            .empty().append(opt.hoursLabel);
        cntr.find(".abDurSelectTimeLabelsCntr .abDurSelectRightPane")
            .empty().append(opt.minutesLabel);
        cntr.find("#abDurSelectSetButton a").empty().append(opt.setButtonLabel);
        if (opt.onBeforeShow) {
            opt.onBeforeShow(i, cntr);
        }
        cntr.slideDown("fast");
            
    };// END openCntr()
        
    /**
     * Closes (hides it) the popup container.
     * @private
     * @param {Object} i    -   Optional. The input field for which the
     *                          container is being closed.
     * @return {undefined}
     */
    jQuery.abDurSelect.closeCntr = function(i) {
        var e = $("#abDurSelectCntr");
        if (e.is(":visible") == true) {
            
            // If IE, then check to make sure it is realy visible
            if (jQuery.support.tbody == false) {
                if (!(e[0].offsetWidth > 0) && !(e[0].offsetHeight > 0) ) {
                    return;
                }
            }
            
            jQuery('#abDurSelectCntr')
                .css("display", "none")
                .removeClass()
                .css("width", "");
            if (!i) {
                i = $(".isabDurSelectActive");
            }
            if (i) {
                var opt = jQuery(i).removeClass("isabDurSelectActive")
                            .data("abDurSelectOptions");
                if (opt && opt.onClose) {
                    opt.onClose(i);
                }
            }
        }
        return;
    };//end closeCntr()
    
    /**
     * Closes the timePicker popup if user is not longer focused on the
     * input field or the timepicker
     * 
     * @private
     * @param {jQueryEvent} ev -    Event passed in by jQuery
     * @return {undefined}
     */
    jQuery.abDurSelect._doCheckMouseClick = function(ev){
        if (!$("#abDurSelectCntr:visible").length) {
            return;
        }
        if (   !jQuery(ev.target).closest("#abDurSelectCntr").length
            && jQuery(ev.target).not("input.isabDurSelectActive").length ){
            jQuery.abDurSelect.closeCntr();
        }
        
    };// jQuery.abDurSelect._doCheckMouseClick
    
    /**
     * FUNCTION: $().abDurSelect()
     * Attaches a abDurSelect widget to each matched element. Matched
     * elements must be input fields that accept a values (input field).
     * Each element, when focused upon, will display a time selection 
     * popoup where the user can define a time.
     * 
     * @memberOf jQuery
     * 
     * PARAMS:
     * 
     * @param {Object}      [opt] - An object with the options for the time selection widget.
     * 
     * @param {String}      [opt.containerClass=""] - A class to be associated with the popup widget.
     * 
     * @param {String}      [opt.containerWidth=""] - Css width for the container.
     * 
     * @param {String}      [opt.hoursLabel="Hours"] - Label for the Hours.
     * 
     * @param {String}      [opt.minutesLabel="Minutes"] - Label for the Mintues container.
     * 
     * @param {String}      [opt.setButtonLabel="Set"] - Label for the Set button.
     * 
     * @param {String}      [opt.popupImage=""] - The html element (ex. img or text) to be appended next to each
     *      input field and that will display the time select widget upon
     *      click.
     * 
     * @param {Integer}     [opt.zIndex=10] - Integer for the popup widget z-index.
     * 
     * @param {Function}    [opt.onBeforeShow=undefined] - Function to be called before the widget is made visible to the 
     *      user. Function is passed 2 arguments: 1) the input field as a 
     *      jquery object and 2) the popup widget as a jquery object.
     * 
     * @param {Function}    [opt.onClose=undefined] - Function to be called after closing the popup widget. Function
     *      is passed 1 argument: the input field as a jquery object.
     * 
     * @param {Bollean}     [opt.onFocusDisplay=true] - True or False indicating if popup is auto displayed upon focus
     *      of the input field.
     * 
     * 
     * RETURN:
     * @return {jQuery} selection
     * 
     * 
     * 
     * EXAMPLE:
     * @example
     *  $('#fooTime').abDurSelect();
     * 
     */
    jQuery.fn.abDurSelect = function (opt) {
        return this.each(function(){
            if(this.nodeName.toLowerCase() != 'input') return;
            var e = jQuery(this);
            if (e.hasClass('hasabDurSelect')){
                return this;
            }
            var thisOpt = {};
            thisOpt = $.extend(thisOpt, jQuery.abDurSelect.options, opt);
            e.addClass('hasabDurSelect').data("abDurSelectOptions", thisOpt);
            
            //Wrap the input field in a <div> element with
            // a unique id for later referencing.
            if (thisOpt.popupImage || !thisOpt.onFocusDisplay) {
                var img = jQuery('<span>&nbsp;</span><a href="javascript:" onclick="' +
                        'jQuery.abDurSelect.openCntr(jQuery(this).data(\'abDurSelectEle\'));">' +
                        thisOpt.popupImage + '</a>'
                    )
                    .data("abDurSelectEle", e);
                e.after(img);
            }
            if (thisOpt.onFocusDisplay){
                e.focus(function(){
                    if (!this.classList.contains("isabDurSelectActive")) {
                        jQuery.abDurSelect.openCntr(this);
                    }
                });
                e.blur(function(event){
                    clicked = jQuery(event.relatedTarget);
                    if (clicked.hasClass("abDurSelectMin")) return;
                    if (clicked.hasClass("abDurSelectHr")) return;
                    if (clicked.hasClass("abDurSelectAmPm")) return;
                    if (clicked.is("#abDurSelectSetLink")) return;
                    jQuery.abDurSelect.closeCntr(this);
                });
            }
            return this;
        });
    };// End of jQuery.fn.abDurSelect
    
})(jQuery);
