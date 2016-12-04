LEGO WeDo 2.0 Extension for Scratch 2
=====================================

Introduction
------------

[LEGO WeDo 2.0](https://education.lego.com/en-au/learn/elementary/wedo-2/product-range) is a product range
of the LEGO Education series for teaching basic engineering and programming to kids at the age of 7+.
It communicates through [Bluetooth Low Energy](https://en.wikipedia.org/wiki/Bluetooth_low_energy)
and can be programmed with [Scratch 2](https://scratch.mit.edu/wedo), allowing robotic and non-robotic
projects to be implemented in the same visual programming language. Unofficial support for Linux is
available through the [S2Bot helper app](http://www.picaxe.com/Teaching/Other-Software/Scratch-Helper-Apps/), but only works with the [Bluegiga BLED112 Bluetooth Smart Dongle](http://www.silabs.com/products/wireless/bluetooth/bluetooth-smart-modules/Pages/bled112-bluetooth-smart-dongle.aspx). 

This project provides an open source Scratch 2 HTTP extension for LEGO WeDo 2.0 which should work with
any Bluetooth LE capable chip supported by Linux.   

Installation
------------

For now this project doesn't provide Scratch 2 blocks. You can re-use the templates provided by S2Bot.

1. Install prerequisites of [pygattlib](https://bitbucket.org/OscarAcena/pygattlib) as listed in its [DEPENDS](https://bitbucket.org/OscarAcena/pygattlib/raw/a858e8626a93cb9b4ad56f3fb980a6517a0702c6/DEPENDS) file.
2. Install prerequisites of the extension:

        pip install -r requirements.txt

3. Download and extract [S2Bot](http://www.picaxe.com/downloads/s2bot/LinS2Bot.tar.gz), only needed for Scratch 2 templates.

Usage
----- 

1. Determine the MAC address of your LEGO WeDo 2.0 Hub:

        sudo hcitool lescan

2. Start the Wedo 2.0 extension with the determined MAC address:

        ./scratch2-wedo2.py MAC_ADDRESS

   Depending on your permissions you might have to run it with sudo:

        sudo ./scratch2-wedo2.py MAC_ADDRESS

3. Start Scratch 2.

4. Open `wedo2_template.sb2` from S2Bot.

5. Save your project under a different name.

6. The LEGO Wedo 2.0 blocks are now available under `Other blocks`.

Notes
-----

At the moment only light and motor controls are working.
