/*
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  Ontology Engineering Group
        http://www.oeg-upm.net/
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  Copyright (C) 2017 Ontology Engineering Group.
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
  GeoLinkeddata Open Data Portal is licensed under a
  Creative Commons Attribution-NC 4.0 International License.
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
*/

// Add listener to element
var addListener = function addListener(elem, type, fn)
{
    if (elem.addEventListener) elem.addEventListener(type, fn, false);
    else if (elem.attachEvent)
    {
        elem.attachEvent("on" + type, function()
        {
            return fn.call(elem, window.event);
        });
    }
    else elem["on" + type] = fn;
};

// Stop bubble and propagation of the event
var stopPropagation = function stopPropagation(e)
{
    if (typeof e['preventDefault'] === "function") e['preventDefault']();
    if (typeof e['stopPropagation'] === "function") e['stopPropagation']();
    else e['cancelBubble'] = true;
};

// Get Cookie value
var getCookie = function getCookie(name)
{
    var nameEQ = name + "=";
    var ca = document['cookie']['split'](';');
    for(var i = 0;i < ca['length'];i++) {
        var c = ca[i];
        while (c['charAt'](0) === ' ') c = c['substring'](1, c['length']);
        if (c['indexOf'](nameEQ) === 0) return c['substring'](nameEQ['length'], c['length']);
    }
    return null;
};

// Get Query Parameters
var getParameterByName = function getParameterByName(name)
{
    var url = window.location.href, n = name['replace'](/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + n + "(=([^&#]*)|&|#|$)"),
        results = regex['exec'](url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2]['replace'](/\+/g, " "));
};

// Get Path URL
var getURL = function getURL()
{
    return location['protocol'] + '//' + location['hostname'] + 
        (location['port'] ? ':' + location['port'] : '');
};

// Get if browser is mobile
var detectMobile = function detectMobile()
{
    var a = navigator['userAgent']||navigator['vendor']||window['opera'];
    var m = false;
    if(/(|android|ipad|playbook|silk|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))) return true;
    return m;
};

// Convert links for Mobile Web Standalone App
if(("standalone" in window['navigator']) && window['navigator']['standalone'])
{
    var noddy, remotes = false;
    addListener(document, 'click', function(e)
    {
        noddy = e['target'];
        while(noddy['nodeName'] !== "A" && noddy['nodeName'] !== "HTML")
        {
            noddy = noddy['parentNode'];
        }
        if('href' in noddy && noddy['href']['indexOf']('http') !== -1 &&
            (noddy['href']['indexOf'](document['location']['host']) !== -1 || remotes))
        {
            stopPropagation(e);
            document['location']['href'] = noddy['href'];
        }
    });
}

// Generate DOM is ready
window['readyHandlers'] = [];
window['ready'] = function ready(handler)
{
    window['readyHandlers']['push'](handler);
    handleState();
};
window['handleState'] = function handleState ()
{
    if (['interactive', 'complete']['indexOf'](document['readyState']) > -1)
    {
        while(window['readyHandlers']['length'] > 0)
            (window['readyHandlers']['shift']())();
    }
};
document['onreadystatechange'] = window['handleState'];

// Update navigation order
var updateNavigation = function updateNavigation()
{
    for (var i = 0; i < 5; i++)
    {
        var elem = document['getElementsByClassName']('ord' + i);
        for (var j = 0; j < elem['length']; j++)
        {
            var classes = '';
            for (var k = 0; k < elem[j]['classList']['length']; k++)
            {
                classes += elem[j]['classList'][k];
                if (elem[j]['classList'][k]['includes']('ord')) break;
                classes += ' ';
            }
            elem[j]['className'] = classes;
        }
    }
};

// Add or Remove one navigation order to element
var updateElementOrder = function updateElementOrder(elem, add)
{
    var elemClass = elem['className'];
    if (add === true)
    {   
        if (elemClass !== '') elemClass += ' ';
        elemClass += 'menu-shown';
    }
    else elemClass = elemClass.replace('menu-shown', '');
    elem['className'] = elemClass;
};

// Update HTML class
document['documentElement']['className'] = document['documentElement']['className'].replace('no-js', 'js');

/* ################################################################## */

var burguerHandler = function burguerHandler(e)
{
    // Stop bubble
    stopPropagation(e);

    // Update class to the button
    var elem = document['getElementById']('burguer-button');
    var elemClass = elem['className'];
    if (elemClass['includes']('fa-bars'))
        elemClass = elemClass['replace']('-bars', '-remove');
    else elemClass = elemClass['replace']('-remove', '-bars');
    elem['className'] = elemClass;

    // Update class to the container and order navigation
    var mainElem = document['getElementById']('main-container');
    var footElem = document['getElementById']('footer-container');
    elem = document['getElementById']('burguer-container');
    elemClass = elem['className'];
    if (elemClass['includes']('shown'))
    {
        elemClass = elemClass['replace']('shown', '');
        updateElementOrder(mainElem, false);
        updateElementOrder(footElem, false);
    }
    else
    {
        elemClass += 'shown';
        updateElementOrder(mainElem, true);
        updateElementOrder(footElem, true);
    }
    elem['className'] = elemClass;
};

// Execute when DOM is Ready
ready(function()
{
    // Assign handler to hamburguer
    var buButton = document['getElementById']('burguer-button');
    if (buButton !== null && buButton['style']['display'] !== 'none')
    {
        addListener(buButton, 'click', burguerHandler);
    }
});
