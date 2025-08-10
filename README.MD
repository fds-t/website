# Website

This is my website. I have barely ever used html/css, so please enjoy all the horrible code to your heart's content.

## Building

As of right now, the website is hosted at [neocities](https://neocities.org). Since neocities only hosts static sites, you have to generate it yourself.

Now, a sensible person would likely use an already existing static site generator such as jekyll, however, I don't care, so instead I'm using my own strange python script to do it for me (warning: script is very hacky!)

Run it like so:

```
~ $ python3 generate.py -i src/ -o build/
```

And upload it:

```
~ $ neocities push build/
```
