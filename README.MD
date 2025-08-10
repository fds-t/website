# Website

This the repo for my website. I have barely ever used html/css, so please enjoy all the horrible code to your heart's content.

## Building

As of right now, the website is hosted at [neocities](https://neocities.org). Since neocities only hosts static sites, you have to generate it yourself.

Now, a sensible person would likely use an already existing static site generator such as jekyll, however, I don't care, so instead I'm using my own strange python script to do it for me (warning: script is very hacky!)

Run it like so:

```sh
# Build site, including bsky integration
~ $ python3 generate.py -i src/ -o build/

# Or, if bsky integration has already been generated before:
~ $ python3 generate.py -i src/ -o build/ --ignore_bsky
```

And upload it:

```sh
~ $ neocities push build/site/
```
