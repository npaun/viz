# viz
prettier, faster and hopefully better GTFS visualizer.

<img src="https://raw.githubusercontent.com/npaun/viz/master/docs/viz-screenshot.png" width="1000" />

## Requirements

* Python 3 with `pip`
* A C++ compiler
* A Mapbox key [[Create account here, if needed](https://account.mapbox.com/auth/signup/)]

## To run

1. `git clone https://github.com/jsteelz/viz`
2. `cd viz`
3. Get a Mapbox API key and set it in `js/config.js'
4. `make`
5. `./visualizer.py <path to GTFS files>`

### Manual installation of Python dependencies
You can also install the Python dependencies by `pip install geojson flask`.

## How fast is it?

Benchmarks were performed on a laptop with 16 GB of RAM and 6 core processor. All times are approximative depending on the precise GTFS data used for each feed.

| Feed                     | Time (s) |
|--------------------------|----------|
| MTA Subway               | 4        |
| TTC                      | 18       |

## For more info
* <https://jsteelz.github.io/gtfs-viz> (coming soon maybe ???????? 🙏)
* <https://npaun.io/viz> (coming soon, even more maybe ?????)

