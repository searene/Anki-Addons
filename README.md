# Anki-Addons
This repository is used to store all kinds of anki addons that I created

It contains the following addons till now:

1. ImageResizer
2. PurgeAttribute
3. GoldenDictMedia

# How to use it

Put the respective `.py` file in your Anki addon folder and restart it. Some of these addons are uploaded to [ankiweb](https://ankiweb.net/shared/addons/), you can install them from there directly.

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

### Usage
Put all the files under `PurgeAttributes`(including `PurgeAttributes.py` and `PurgeAttribues` folder which contains `bs4`) into your Anki add-ons folder.

### Effects
It will purge the four attributes by default:

* font-family
* font-size
* background-color
* line-height

If you are running Anki with a high-resolution like me, and you didn't strip the html when pasting like me, you may encounter something like this:

![without PurgeAttributes](http://i.imgur.com/jQTDGaG.png)

If you use the addon, it will remove the yellow background and remove the `font-size` attribute, because the font size here is small. The result is like this:

![with PurgeAttributes](http://i.imgur.com/wdbtrFa.png)

Now it's not hard to see, right?

### Configuration

To choose which attribute you need to remove, edit the `purgeAttributes.py` file from menu `Tools --> Add-ons --> PurgeAttributes --> Edit`, and modify the variable `REMOVE_ATTRIBUTES` at will.

## GoldenDictMedia

### Introduction

The addon is used to import audios and images from `goldendict` directly when copying and pasting from it. For example, for the following text:

![goldendict](http://i.imgur.com/0Vu6v4N.png)

if you copy the definitions directly into anki, you will find that the pronounciations and pictures will not be recognized by Anki. This is because the paths of those audios and images are not set correctly. Usually it's started with "gdau://". Copy the entire definition in it, and paste it in Anki, then hit `Ctrl + Shift + X` to Edit HTML, find the part containing "gdau://", mine's are like this

```html
...<a href="gdau://e73293ef041cad84654c62963f7b6bb7/ame_apple1.wav">...
```

Copy the part after `gadu://` immediately, which is `e73293ef041cad84654c62963f7b6bb7` in my case. Then add it in the `GoldenDictMedia.py` file in your Anki addon folder:

```python
addressMap = {'e73293ef041cad84654c62963f7b6bb7': '/media/OS/Dictionaries/longman5/En-En-Longman_DOCE5.dsl.dz.files', 
        '4f74aab894b66b99af88061eadcf5104': '/media/OS/Dictionaries/Webster\'s Collegiate Dictionary/Webster\'s Collegiate Dictionary.dsl.files'}
```

This is a map, what `e73293ef041cad84654c62963f7b6bb7` refers to is the path which contains all the audios and images of the dictionary. This is usually a `dz` file, you may need to uncompress it beforehand. Here I added two dictionaries. The addon will replace the `gdau://...` part with the real one and import the media.

# Known Issues

PurgeAttributes is ridiculously slow on Windows XP. Haven't found a solution yet.

# License

MIT
