# Find the Shortest Path Between Multiple Stops in Prague

Python script for searching the shortest path between multiple Prague city transport stops.

GTFS data source:

* <https://pid.cz/o-systemu/opendata/>

## Background

This project started with simple question. Where should we met to go for a beer?

I live in Prague and have friends all over the place. We want to find the closest place to go for a beer with public transport from everyone's home.

## Implementation

I found a public source of data for Prague Integrated Transport (PID in Czech).

* <https://pid.cz/o-systemu/opendata/>

First, the data must be processed into simpler form. I decided for bus stops list with connections between neighboring stops and their distances.

With this graph of stops we can use breadth-first search algorithm. This will gives us list of all available paths (stop 1 -> stop 2 -> etc) from some home stop.

And if we have more lists for more stops (each one for one of my friends), we can evaluate (based on some optimization function) the best stop for everybody to meet.

## What to Improve

<s>Currently even some exotic connections and stops are included. I have to add a filter only for common day-time connections.</s>

<s>The time needed to transfer between connections is not included.</s>

All is done! The number of transfers algorithm is just a afterthought, so it does not fit into the design. But it works.

## Final Thoughts

It is still just only a estimate and simulation. But the results seems legit. What is ironic is that for me and my friends the best place to meet is right in the center (shocking).

Now all that remains is to select a good pub. Cheers :-).
