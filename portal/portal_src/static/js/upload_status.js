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

// Handler for expand or contract event
var expandSection = function expandSection(e)
{

    // Stop bubble
    stopPropagation(e);

    // Get target of event
    var kindSection = this['id']['split']('-')['pop']();

    // Change class of arrow
    var targetArrow = document['getElementById']('arrow-' + kindSection);
    var targetArrowClass = targetArrow['className'];
    targetArrowClass = (targetArrowClass['indexOf']('double-down') > 0) ?
        targetArrowClass['replace']('double-down', 'double-up') :
        targetArrowClass['replace']('double-up', 'double-down');
    targetArrow['className'] = targetArrowClass;

    // Change class of panel
    var targetPanel = document['getElementById']('messages-panel-' + kindSection);
    var targetPanelClass = targetPanel['className'];
    targetPanelClass = (targetPanelClass['indexOf']('non-expanded') > 0) ?
        targetPanelClass['replace']('non-expanded', 'expanded') :
        targetPanelClass['replace']('expanded', 'non-expanded');
    targetPanel['className'] = targetPanelClass;

};

// Handler for switch
var changeSwitch = function changeSwitch(e)
{

    // Stop bubble
    stopPropagation(e);

    // Get value of target
    var switchValue = this['value'];

    // Get row
    var r = this['parentNode'];

    // Change class of parentNode
    r['className'] = (
        switchValue !== 'disabled'
    ) ? r['className']['replace'](' disabled', '') : r['className'] + ' disabled';

};

// Execute when DOM is Ready
ready(function()
{

    // Possible buttons
    var buttons = ['warn', 'error', 'status'], i;
    for (i = 0; i < buttons['length']; i++)
    {
        // Assign handler to buttons
        var button = document['getElementById']('button-expand-' + buttons[i]);
        if (button !== null)
        {
            addListener(button, 'click', expandSection);
        }
    }

    // Possible inputs with disable
    var switches = document['getElementsByClassName']('field-status-select vf');
    if (switches !== null)
    {
        for (i = 0; i < switches['length']; i++)
        {
            addListener(switches[i], 'change', changeSwitch);
        }
    }

});
