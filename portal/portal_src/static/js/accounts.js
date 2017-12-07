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

// Handler for read more / read less event
var readHandler = function readHandler(e)
{

    // Stop bubble
    stopPropagation(e);

    // Get paragraph container
    var description = document['getElementById']('user-description');

    // Get target of event
    var targetId = e['target']['id'], secondTarget = null;
    var target = document['getElementById'](targetId);

    // Change class of target
    target['className'] = target['className']['replace'](
        'shown', 'hidden'
    );

    // Check what is the target
    if (targetId === 'button-read-more')
    {
        // Change class for paragraph
        description['className'] = 'expanded';

        // Change class for other target
        secondTarget = document['getElementById']('button-read-less');
        secondTarget['className'] = secondTarget['className']
            ['replace']('hidden', 'shown');
    }
    else
    {
        // Change class for target and paragraph
        description['className'] = 'non-expanded';

        // Change class for other target
        secondTarget = document['getElementById']('button-read-more');
        secondTarget['className'] = secondTarget['className']
            ['replace']('hidden', 'shown');
    }
};

// Execute when DOM is Ready
ready(function()
{
    // Assign handler to read more element
    var buButton = document['getElementsByClassName']('buttons-read');
    if (buButton !== null)
    {
        for (var i = 0; i < buButton['length']; i++)
        {
            addListener(buButton[i], 'click', readHandler);
        }
    }
});