This repo contains the source code for the raspberry pi pico w and 2w for testing.

I noticed problems loading html pages for my animation products when I started exploring the pico 2W.

Each is complete code set and files.  

The base case is the pico w using cp 8.2.10.  This does not exibit the problem

There are two test cases one using the pico w and one using the pico 2w they both manifest the issue after loading many times.  It looks like it might be something like a memory leak.

See the logs for examples, in them I printout the memory before sending the html file.  It appears that error happen when the memory gets to a lower value.  This is just an observation.
