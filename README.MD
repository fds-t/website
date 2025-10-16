# Website ![](src/favicon.png)

This the repo for my website. I have barely ever used html/css, so please enjoy all the horrible code to your heart's content.

As of right now, the website is hosted at [neocities](https://neocities.org). Since neocities only hosts static sites, you have to generate it yourself.

Now, a sensible person would likely use an already existing static site generator such as jekyll, however, I don't care, so instead I'm using my own strange python script to do it for me (warning: it is quite hacky!)

## Requirements

A "resource" folder named `res/` is expected to lie in the root of this repository.

### Site generation

Outside of bsky integration, the regular site requires nothing more than what's included with `python3` itself.

For bsky integration, the following libraries are also required:

- `requests`
- `atproto`

Additionally, to be able to fetch the bsky posts, authentication is required. The script expects a file called `bsky_info` containing a username and password separated by a space to lie in the same directory as the `generate.py` script.

### Neocities uploading / cleaning the site

For uploading to and cleaning the site, the `requests` library is required. A file called `neocities_info` containing the api key of the site is expected to lie in the same directory as the `neo.py` script.


## Building

Build the site like so:

```sh
# Build site, including bsky integration
~ $ python3 generate.py -i src/ -o build/

# Or, if bsky integration has already been generated before
# (or to simply skip the bsky integration altogether)
~ $ python3 generate.py -i src/ -o build/ --ignore_bsky
```

And upload it:

```sh
# Upload everything in the build/site/ directory
~ $ python3 neo.py upload -o build/site/

# Or, do a 'clean' upload of everything
# (removes all files not in the local build/site/ directory)
~ $ python3 neo.py cleanupload -o build/

# This is the same as running:
# ~ $ python3 neo.py clean -o build/
# ~ $ python3 neo.py upload -o build/
```