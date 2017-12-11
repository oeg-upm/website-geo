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

var pictureImgValue = null,
    pictureImgObject = null,
    pictureImgTester = null;

// Handler for picture input event
var changePictureInput = function changePictureInput(e)
{

    // Break flow if ready is not working
    if (pictureImgObject === null || pictureImgTester === null) return;

    // Stop bubble
    stopPropagation(e);

    // Save SRC for image
    pictureImgValue = e['target']['value'];
    pictureImgTester.src = pictureImgValue;
};

// Handler for picture input event - success
var changePictureInputSuccess = function changePictureInputSuccess(e)
{
    // Stop bubble
    stopPropagation(e);

    // Change SRC for image
    pictureImgObject.src = pictureImgValue;

    // Change class of input to show
    var p = document.getElementById('picture');
    p.className = '';

    // Change value of input flag
    var pf = document.getElementById('input-picture-flag');
    pf.value = 'true';
};

// Handler for picture input event - error
var changePictureInputError = function changePictureInputError(e)
{
    // Stop bubble
    stopPropagation(e);

    // Change class of input to show error
    var p = document.getElementById('picture');
    p.className = 'failed';

    // Change value of input flag
    var pf = document.getElementById('input-picture-flag');
    pf.value = 'false';
};

// Execute when DOM is Ready
ready(function()
{
    // Get IMG object
    pictureImgObject = document.getElementById('input-picture-img');

    // Assign handler to photo picture img
    if (pictureImgObject !== null)
    {
        pictureImgTester = new Image();
        pictureImgTester['onerror'] = changePictureInputError;
        pictureImgTester['onabort'] = changePictureInputError;
        pictureImgTester['onload'] = changePictureInputSuccess;
    }

    // Assign handler to photo picture input
    var photoInput = document.getElementById('input-picture');
    if (photoInput !== null)
    {
        addListener(photoInput, 'keyup', changePictureInput);
    }
});