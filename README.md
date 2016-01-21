# Anki-Addons
This repository is used to store all kinds of anki addons that I created

It contains the following addons till now:

1. ImageResizer
2. PurgeAttribute

## 1. ImageResizer

### Introduction

ImageResizer is a simple anki addon used to resize the image stored in the clipboard. So images that are too big or too small to be used in reviewing are not a problem any more.

##### Before resizing

![Before resizing](http://i.imgur.com/54kbvhl.jpg)

##### After resizing

![After resizing](http://i.imgur.com/hQ1zeMU.png)

### Usage

Normally after you installed this addon, Images will be automatically resized if you paste images when adding new cards, either by hitting `Ctrl + V` or `Ctrl + Shift + V` or click on the button on the toolbar.

![To make it work](https://i.imgur.com/kupbkcU.png)

### Settings
You can change the shortcut and the size of the image etc. from `Tools --> Image Resizer`

![Start settings from menu](http://i.imgur.com/ylv6iQK.png)

The `Settings` window will pop up.

![Settings](https://i.imgur.com/h0elRHu.png)

Check `Automatically resize the image when pasting` if you want to paste the resized image when using `Ctrl+V`. Anki will paste the original-sized image if you uncheck it.

The `Key Combination` is the shortcut to paste the resized image. It's just like `Ctrl+V`, the only difference is that you will always get the resized the image if you use the shortcut to paste. You can modify the shortcut by hitting the button `Grab the Key combination` on the right. **Notice that the shortcut you specified may not work, try and find a workable one.**

You can also set the width or height of the resized image. Select `scale to width and keep ratio`, it will resize the image according to the width you specified, and the height value here will be ignored. The same goes to `scale to height and keep ratio`. Notice that it will always keep the original image's ratio, either by width or height.

## 2. PurgeAttributes
### Introduction
PurgeAttributes is used to purge the `font-size` attribute originally. But you can purge any attribute defined in something like `style='font-size: 100px; color: red'`.

### Effects
It will purge the four attributes by default:

* 'font-family',
* 'font-size',
* 'background-color',
* 'line-height',

If you are running Anki with a high-resolution like me, and you didn't strip the html when pasting like me, you may encounter something like this:

![without PurgeAttributes](http://i.imgur.com/jQTDGaG.png)

If you use the addon, it will remove the yellow background and remove the `font-size` attribute, because the font size here is small. The result is like this:

![with PurgeAttributes](http://i.imgur.com/wdbtrFa.png)

Now it's not hard to see, right?

### configuration

To choose which attribute you need to remove, edit the `purgeAttributes.py` file from menu `Tools --> Add-ons --> PurgeAttributes --> Edit`, and modify the variable `REMOVE_ATTRIBUTES` at will.

# Issues

Issues and requests to improve the addon are always welcomed.

# License

MIT
