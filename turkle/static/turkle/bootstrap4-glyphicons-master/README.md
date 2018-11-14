# bootstrap4-glyphicons

How to use Glyphicons with Bootstrap 4 (without getting mad)

For further info & samples, read the [official page](https://www.ryadel.com/en/bootstrap-3-glyphicons-halflings-set-bootstrap4-fontawesome/).

## Introduction

If you stumbled upon this project you most likely already know Bootstrap, the award-winning and worldwide-renown open source toolkit for developing with HTML, CSS, and JS. As a matter of fact, you are probably struggling trying to switch from from Bootstrap 3 to Bootstrap 4. Among the many things that have changed (mostly summarized in the [official Migration guide](http://getbootstrap.com/docs/4.0/migration/)) there was the choice to drop the Glyphicons icon font. 

If you need icons, the Bootstrap team suggest one of the following alternatives:

* the upstream version of [Glyphicons](https://glyphicons.com/)
* [Octicons](https://octicons.github.com/)
* [Font Awesome](https://fontawesome.com/)
* Other alternatives mentioned in the [Extend page](https://getbootstrap.com/docs/4.0/extend/icons/)

If you're migrating an existing website based on Bootstrap 3, the first option definitely seems the most viable one. However, the Glyphicons Basic set - the one available for free - does not cover all the icons which were available in Bootstrap, which open-source toolkit was granted with the permissions to use the Halflings set (as long as they provide a link and credits info). 

Now, since Bootstrap 4 doesn't ship the Halflings set anymore, if you want to use that set you might need to pay: if you don't want to, you are basically forced to migrate from Glyphicons to a viable open-source alternative, such as the aforementioned Octicons and Font Awesome - the latter being personal preference, as its free set is good enough for most projects. However, that will undoubtely require some major HTML code rewrite, because you'll have to perform a manual mapping from something like this:

    <span class="glyphicons glyphicons-home"></span>
    <span class="glyphicons glyphicons-plus-sign"></span>
    <span class="glyphicons glyphicons-hand-left"></span>

to something like this (in case of **FontAwesome**):

    <span class="fas fa-home"></span>
    <span class="fas fa-plus-circle"></span>
    <span class="fas fa-hand-point-left"></span>

... and so on. Unfortunately, as you might see, the icon names might also be quite different, hence is not possible to search-and-replace them easily.


## Alternatives

If you're building a brand new project, I strongly suggest to drop the Glyphicons package and to migrate to FontAwesome: not only you'll have more icons, but you'll also have the chance to seamlessly switch from Font icons to SVG icons,  which is something that you will hardly ever regret (in case you don't know why, read [here](https://www.ianfeather.co.uk/ten-reasons-we-switched-from-an-icon-font-to-svg/)).

However, if you're dealing with an existing project which makes an extensive use of the Glyphicons Halflings set, you can install this package containing two viables workaround.

## Installing

This package can be used in two alternative ways: **Bootstrap 4+3** and **FontAwesome Mapping**.


### Method #1: Bootstrap 4+3

This workaround leverages the fact that you can still use Bootstrap 3.x **in addition** to Bootstrap 4 without any issue of sort, as long as you only get only the "glyphicon part". You won't have any license issues, since you'll be actually using Bootstrap 3. 

To implement this workaround, install the package into your web site and add the following within the `<head>` element:

    <link href="/bootstrap4-glyphicons/css/bootstrap-glyphicons.min.css" rel="stylesheet" type="text/css" />

That's it.


### Method #2: FontAwesome Mapping

Since any Glyphicon image has (more or less) their FontAwesome equivalent, we can map the various `glyphycons*` css classes to their `fa*` equivalent. This is the purpose of the file you can find in `/maps/glyphicons-fontawesome.less` , which will act as a transparent mapping bridge between **Glyphicon** and **FontAwesome**. 

To implement this workaround, install the package into your web site and add the following within the `<head>` element:

    <link href="/bootstrap4-glyphicons/maps/glyphicons-fontawesome.min.css" rel="stylesheet" type="text/css" />

The only caveat here is that you'll have to use the font-based icons instead of the SVG alternative (see above), but if you're a Glyphicon user you won't suffer from that: there's a much higher chance that you won't like the "new" icons... If you feel like that, just implement the **Bootstrap 4+3** alternative instead.


## Authors

* [Darkseal](https://github.com/Darkseal)


## License

This project is licensed under the APACHE 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

