# Anki-Addons
This repository is used to store all kinds of anki addons that I created

It contains the following addons till now:

1. ImageResizer

## 1. ImageResizer

### Introduction

ImageResizer is a simple anki addon used to resize the image stored in the clipboard. So images that are too big or too small to be used in reviewing are not a problem any more.

### Usage

Normally after you installed this addon, Images will be automatically resized if you paste images when adding new cards, either by hitting `Ctrl + V` or `Ctrl + Shift + V` or click on the button on the toolbar.

![To make it work](https://i.imgur.com/kupbkcU.png)

### Settings
You can change the shortcut and the size of the image etc. from `Tools --> Image Resizer`

![Start settings from menu](http://i.imgur.com/ylv6iQK.png)

The `Settings` window will pop up.

![Settings](https://i.imgur.com/h0elRHu.png)

Check `Automatically resize the image when pasting` if you want to paste the resized image when using `Ctrl+V`. Anki will paste the original-sized image if you uncheck it.

The `Key Combination` is the shortcut to paste the resized. It's just like `Ctrl+V`, the only difference is that you will always get the resized the image if you use the shortcut to paste. You can modify the shortcut by hitting the button `Grab the Key combination` on the right. **Notice that the shortcut you specified may not work, try and find a workable one.**

You can also set the width or height of the resized image. Select `scale to width and keep ratio`, it will resize the image according to the width you specified, and the height value here will be ignored. The same goes to `scale to height and keep ratio`. Notice that it will always keep the original image's ratio, either by width or height.

### Issues

Issues and requests to improve the addon are always welcomed.

### License

MIT
